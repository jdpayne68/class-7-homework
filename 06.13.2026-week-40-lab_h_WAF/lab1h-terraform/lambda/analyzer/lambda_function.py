from __future__ import annotations

import json
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

WAF_LOG_GROUP = os.environ["WAF_LOG_GROUP"]
DYNAMODB_TABLE = os.environ["DYNAMODB_TABLE"]
BEDROCK_MODEL_ID = os.environ["BEDROCK_MODEL_ID"]
LOOKBACK_MINUTES = int(os.environ.get("LOOKBACK_MINUTES", "10"))
MAX_EVENTS = int(os.environ.get("MAX_EVENTS", "5"))
BEDROCK_MAX_TOKENS = int(os.environ.get("BEDROCK_MAX_TOKENS", "1100"))

logs = boto3.client("logs")
bedrock = boto3.client("bedrock-runtime")
table = boto3.resource("dynamodb").Table(DYNAMODB_TABLE)


def iso_timestamp(value: Any) -> str:
    try:
        milliseconds = int(value)
    except (TypeError, ValueError):
        return str(value)

    return datetime.fromtimestamp(
        milliseconds / 1000,
        tz=timezone.utc,
    ).isoformat()


def get_recent_waf_events() -> list[dict[str, Any]]:
    end_time = int(time.time() * 1000)
    start_time = int(
        (
            datetime.now(timezone.utc)
            - timedelta(minutes=LOOKBACK_MINUTES)
        ).timestamp()
        * 1000
    )

    response = logs.filter_log_events(
        logGroupName=WAF_LOG_GROUP,
        startTime=start_time,
        endTime=end_time,
        limit=max(MAX_EVENTS * 5, 25),
    )

    events: list[dict[str, Any]] = []

    for log_event in response.get("events", []):
        try:
            waf_event = json.loads(log_event.get("message", ""))
        except json.JSONDecodeError:
            continue

        events.append(
            {
                "cloudwatch_event_id": log_event.get("eventId"),
                "waf_event": waf_event,
            }
        )

    return events


def summarize_waf_event(
    cloudwatch_event_id: str,
    waf_event: dict[str, Any],
) -> dict[str, Any]:
    request = waf_event.get("httpRequest", {})

    return {
        "event_id": cloudwatch_event_id,
        "timestamp": iso_timestamp(waf_event.get("timestamp")),
        "action": waf_event.get("action"),
        "terminating_rule_id": waf_event.get("terminatingRuleId"),
        "terminating_rule_type": waf_event.get("terminatingRuleType"),
        "client_ip": request.get("clientIp"),
        "country": request.get("country"),
        "method": request.get("httpMethod"),
        "uri": request.get("uri"),
        "args": request.get("args"),
    }


def already_processed(event_id: str) -> bool:
    response = table.get_item(
        Key={"event_id": event_id},
        ProjectionExpression="event_id",
        ConsistentRead=True,
    )
    return "Item" in response


def build_prompt(summary: dict[str, Any]) -> str:
    return f"""
Analyze this AWS WAF security event as a cautious SOC analyst assistant.

Event:
{json.dumps(summary, indent=2)}

Provide all six sections:
1. Severity with a brief justification.
2. Likely attack type.
3. Why AWS WAF flagged or blocked the request.
4. Prioritized analyst actions.
5. Concise executive summary.
6. Recommended defensive controls.

Formatting requirements:
- Use Markdown headings and short bullet lists.
- Do not use Markdown tables.
- Keep the complete response under 650 words.
- Complete all six sections before ending.

Important constraints:
- Treat this as analyst assistance, not an autonomous security decision.
- Do not claim compromise without corroborating evidence.
- Clearly identify uncertainty and missing telemetry.
- Do not recommend automatically blocking an account or IP based on this event alone.
""".strip()


def call_bedrock(summary: dict[str, Any]) -> dict[str, Any]:
    try:
        response = bedrock.converse(
            modelId=BEDROCK_MODEL_ID,
            system=[
                {
                    "text": (
                        "You are a cautious SOC analyst assistant. "
                        "Interpret AWS WAF telemetry for a human analyst. "
                        "Never present uncertain inferences as confirmed facts."
                    )
                }
            ],
            messages=[
                {
                    "role": "user",
                    "content": [{"text": build_prompt(summary)}],
                }
            ],
            inferenceConfig={
                "maxTokens": BEDROCK_MAX_TOKENS,
                "temperature": 0.1,
            },
        )

        content = (
            response.get("output", {})
            .get("message", {})
            .get("content", [])
        )
        analysis = "\n".join(
            block["text"]
            for block in content
            if isinstance(block, dict)
            and isinstance(block.get("text"), str)
        ).strip()

        if not analysis:
            raise RuntimeError("Bedrock returned no text content")

        return {
            "status": "SUCCESS",
            "model_id": BEDROCK_MODEL_ID,
            "analysis": analysis,
            "usage": response.get("usage", {}),
            "stop_reason": response.get("stopReason"),
        }

    except (BotoCoreError, ClientError, RuntimeError) as exc:
        return {
            "status": "FAILED",
            "model_id": BEDROCK_MODEL_ID,
            "error": str(exc),
        }


def save_finding(
    summary: dict[str, Any],
    enrichment: dict[str, Any],
) -> None:
    table.put_item(
        Item={
            **summary,
            "ai_status": enrichment.get("status", "UNKNOWN"),
            "ai_model_id": enrichment.get("model_id", BEDROCK_MODEL_ID),
            "ai_analysis": enrichment.get("analysis", ""),
            "ai_stop_reason": enrichment.get("stop_reason", ""),
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        },
        ConditionExpression="attribute_not_exists(event_id)",
    )


def lambda_handler(
    event: dict[str, Any],
    context: Any,
) -> dict[str, Any]:
    recent_events = get_recent_waf_events()

    blocked_events = [
        entry
        for entry in recent_events
        if entry["waf_event"].get("action") == "BLOCK"
        and "httpRequest" in entry["waf_event"]
    ][:MAX_EVENTS]

    findings: list[dict[str, Any]] = []
    skipped_existing = 0
    bedrock_successes = 0
    bedrock_failures = 0

    for entry in blocked_events:
        event_id = entry.get("cloudwatch_event_id")

        if not event_id or already_processed(event_id):
            skipped_existing += 1
            continue

        summary = summarize_waf_event(
            event_id,
            entry["waf_event"],
        )
        enrichment = call_bedrock(summary)

        if enrichment["status"] == "SUCCESS":
            bedrock_successes += 1
        else:
            bedrock_failures += 1

        try:
            save_finding(summary, enrichment)
        except ClientError as exc:
            if (
                exc.response.get("Error", {}).get("Code")
                == "ConditionalCheckFailedException"
            ):
                skipped_existing += 1
                continue
            raise

        finding = {
            **summary,
            "ai_enrichment": enrichment,
        }
        findings.append(finding)

        print(
            json.dumps(
                {
                    "level": "ALERT",
                    "finding_type": "WAF_BLOCKED_REQUEST",
                    **finding,
                }
            )
        )

    result = {
        "request_id": getattr(context, "aws_request_id", "unknown"),
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "events_examined": len(recent_events),
        "blocked_events_found": len(blocked_events),
        "events_processed": len(findings),
        "events_skipped_existing": skipped_existing,
        "bedrock_successes": bedrock_successes,
        "bedrock_failures": bedrock_failures,
        "findings": findings,
    }

    print(json.dumps({"level": "INFO", "analyzer_summary": result}))
    return result
