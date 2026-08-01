from __future__ import annotations

import json
import os
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

TABLE_NAME = os.environ["TOKEN_TABLE_NAME"]
table = boto3.resource("dynamodb").Table(TABLE_NAME)


def response(status_code: int, body: dict[str, object]) -> dict[str, object]:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def get_header(headers: dict[str, str] | None, name: str) -> str | None:
    for key, value in (headers or {}).items():
        if key.lower() == name.lower():
            return value
    return None


def lambda_handler(event: dict[str, object], context: object) -> dict[str, object]:
    token_id = get_header(event.get("headers"), "x-token-id")
    if not token_id:
        return response(400, {"message": "Missing x-token-id header"})

    claims = (
        event.get("requestContext", {})
        .get("authorizer", {})
        .get("claims", {})
    )
    username = claims.get("cognito:username") or claims.get("username")
    if not username:
        return response(403, {"message": "Authenticated username claim is missing"})

    now = datetime.now(timezone.utc).isoformat()

    try:
        result = table.update_item(
            Key={"token_id": token_id},
            UpdateExpression="SET used = :used, used_at = :used_at",
            ConditionExpression="attribute_exists(token_id) AND username = :username",
            ExpressionAttributeValues={
                ":used": True,
                ":used_at": now,
                ":username": username,
            },
            ReturnValues="ALL_NEW",
        )
    except ClientError as exc:
        if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return response(
                403,
                {"message": "Token identifier is missing or does not belong to this user"},
            )
        raise

    print(
        json.dumps(
            {
                "request_id": getattr(context, "aws_request_id", "unknown"),
                "username": username,
                "token_id": token_id,
                "telemetry_decision": "MARKED_USED",
            }
        )
    )

    return response(
        200,
        {
            "message": "Protected request accepted",
            "token_id": token_id,
            "used": result["Attributes"]["used"],
            "used_at": result["Attributes"]["used_at"],
        },
    )
