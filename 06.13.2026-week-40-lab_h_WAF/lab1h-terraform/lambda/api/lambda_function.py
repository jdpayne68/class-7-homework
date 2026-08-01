from __future__ import annotations

import json
from typing import Any


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    request_context = event.get("requestContext", {})
    identity = request_context.get("identity", {})

    body = {
        "message": "Request passed AWS WAF inspection.",
        "path": event.get("path"),
        "method": event.get("httpMethod"),
        "source_ip": identity.get("sourceIp"),
    }

    print(json.dumps({"level": "INFO", "api_request": body}))

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }
