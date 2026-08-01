from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone

import boto3
from boto3.dynamodb.conditions import Attr

TABLE_NAME = os.environ["TOKEN_TABLE_NAME"]
ALERT_AFTER_MINUTES = int(os.environ.get("ALERT_AFTER_MINUTES", "10"))
table = boto3.resource("dynamodb").Table(TABLE_NAME)


def parse_timestamp(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def lambda_handler(event: dict[str, object], context: object) -> dict[str, object]:
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(minutes=ALERT_AFTER_MINUTES)
    alerts: list[dict[str, object]] = []

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
            alert = {
                "level": "ALERT",
                "alert_type": "UNUSED_TOKEN",
                "token_id": item["token_id"],
                "username": item.get("username", "unknown"),
                "issued_at": item["issued_at"],
                "age_minutes": age_minutes,
                "threshold_minutes": ALERT_AFTER_MINUTES,
            }
            alerts.append(alert)
            print(json.dumps(alert))

        last_key = response.get("LastEvaluatedKey")
        if not last_key:
            break
        scan_arguments["ExclusiveStartKey"] = last_key

    summary = {
        "request_id": getattr(context, "aws_request_id", "unknown"),
        "checked_at": now.isoformat(),
        "alert_count": len(alerts),
        "alerts": alerts,
    }

    print(json.dumps({"level": "INFO", "detector_summary": summary}))
    return summary
