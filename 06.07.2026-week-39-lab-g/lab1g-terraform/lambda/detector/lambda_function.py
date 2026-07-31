from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone

import boto3
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import BotoCoreError, ClientError

TABLE_NAME = os.environ["TOKEN_TABLE_NAME"]
ALERT_AFTER_MINUTES = int(os.environ.get("ALERT_AFTER_MINUTES", "10"))
BEDROCK_MODEL_ID = os.environ["BEDROCK_MODEL_ID"]
BEDROCK_MAX_TOKENS = int(os.environ.get("BEDROCK_MAX_TOKENS", "900"))

table = boto3.resource("dynamodb").Table(TABLE_NAME)
bedrock = boto3.client("bedrock-runtime")


def parse_timestamp(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def build_prompt(item: dict[str, object], age_minutes: int) -> str:
    return f"""
Analyze this unused authentication-token event as a SOC analyst assistant.

Event details:
- Username: {item.get("username", "unknown")}
- Token identifier: {item.get("token_id", "unknown")}
- Issued at: {item.get("issued_at", "unknown")}
- Current age: {age_minutes} minutes
- Alert threshold: {ALERT_AFTER_MINUTES} minutes
- Token used: false

Provide all six sections:
1. Severity with a brief justification.
2. Plausible benign explanations.
3. Plausible suspicious explanations.
4. Prioritized analyst actions.
5. Concise executive summary.
6. Recommended remediation controls.

Formatting requirements:
- Use Markdown headings and short bullet lists.
- Do not use Markdown tables.
- Keep the complete response under 700 words.
- Complete all six sections before ending.

Important constraints:
- Treat this as analyst assistance, not an autonomous security decision.
- Do not claim compromise without corroborating evidence.
- Clearly identify uncertainty and missing telemetry.
- Do not recommend automatically disabling the account based on this event alone.
""".strip()


def extract_text(response: dict[str, object]) -> str:
    content = (
        response.get("output", {})
        .get("message", {})
        .get("content", [])
    )
    text_parts = [
        block["text"]
        for block in content
        if isinstance(block, dict) and isinstance(block.get("text"), str)
    ]
    return "\n".join(text_parts).strip()


def enrich_with_bedrock(item: dict[str, object], age_minutes: int) -> dict[str, object]:
    try:
        response = bedrock.converse(
            modelId=BEDROCK_MODEL_ID,
            system=[
                {
                    "text": (
                        "You are a cautious SOC analyst assistant. "
                        "Interpret security telemetry for a human analyst. "
                        "Never present uncertain inferences as confirmed facts."
                    )
                }
            ],
            messages=[
                {
                    "role": "user",
                    "content": [{"text": build_prompt(item, age_minutes)}],
                }
            ],
            inferenceConfig={
                "maxTokens": BEDROCK_MAX_TOKENS,
                "temperature": 0.1,
            },
        )

        analysis = extract_text(response)
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


def lambda_handler(event: dict[str, object], context: object) -> dict[str, object]:
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(minutes=ALERT_AFTER_MINUTES)
    findings: list[dict[str, object]] = []

    scan_arguments: dict[str, object] = {
        "FilterExpression": Attr("used").eq(False),
        "ProjectionExpression": "token_id, username, issued_at, used",
    }

    while True:
        response = table.scan(**scan_arguments)

        for item in response.get("Items", []):
            try:
                issued_at = parse_timestamp(item["issued_at"])
            except (KeyError, TypeError, ValueError) as exc:
                print(
                    json.dumps(
                        {
                            "level": "ERROR",
                            "message": "Invalid token telemetry record",
                            "token_id": item.get("token_id"),
                            "error": str(exc),
                        }
                    )
                )
                continue

            if issued_at >= cutoff:
                continue

            age_minutes = int((now - issued_at).total_seconds() // 60)

            finding: dict[str, object] = {
                "level": "ALERT",
                "alert_type": "UNUSED_TOKEN",
                "token_id": item["token_id"],
                "username": item.get("username", "unknown"),
                "issued_at": item["issued_at"],
                "age_minutes": age_minutes,
                "threshold_minutes": ALERT_AFTER_MINUTES,
            }

            finding["ai_enrichment"] = enrich_with_bedrock(item, age_minutes)
            findings.append(finding)
            print(json.dumps(finding))

        last_key = response.get("LastEvaluatedKey")
        if not last_key:
            break
        scan_arguments["ExclusiveStartKey"] = last_key

    enrichments_succeeded = sum(
        finding["ai_enrichment"]["status"] == "SUCCESS"
        for finding in findings
    )
    enrichments_failed = len(findings) - enrichments_succeeded

    summary = {
        "request_id": getattr(context, "aws_request_id", "unknown"),
        "checked_at": now.isoformat(),
        "finding_count": len(findings),
        "ai_enrichments_succeeded": enrichments_succeeded,
        "ai_enrichments_failed": enrichments_failed,
        "findings": findings,
    }

    print(json.dumps({"level": "INFO", "detector_summary": summary}))
    return summary
