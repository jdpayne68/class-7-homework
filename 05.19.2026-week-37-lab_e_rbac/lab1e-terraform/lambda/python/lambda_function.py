import json
import os
from typing import Any


STUDENT_GROUP = os.environ.get("STUDENT_GROUP_NAME", "students")
ADMIN_GROUP = os.environ.get("ADMIN_GROUP_NAME", "admins")


def normalize_groups(value: Any) -> list[str]:
    """Convert Cognito's groups claim into a predictable list of strings."""
    if isinstance(value, list):
        return [str(group).strip() for group in value if str(group).strip()]

    if not isinstance(value, str) or not value.strip():
        return []

    value = value.strip()

    # Some event formats may contain a JSON-formatted array string.
    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return [
                str(group).strip()
                for group in parsed
                if str(group).strip()
            ]
    except json.JSONDecodeError:
        pass

    # Fall back to values such as "students,admins" or "[students, admins]".
    return [
        group.strip().strip("\"'")
        for group in value.strip("[]").split(",")
        if group.strip()
    ]


def build_response(status_code: int, body: dict[str, Any]) -> dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
        },
        "body": json.dumps(body),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    claims = (
        event.get("requestContext", {})
        .get("authorizer", {})
        .get("claims", {})
    )

    groups = normalize_groups(claims.get("cognito:groups"))
    path = event.get("resource") or event.get("path") or ""

    authenticated_user = (
        claims.get("cognito:username")
        or claims.get("username")
        or claims.get("sub")
        or "unknown"
    )

    if path == "/python":
        allowed = (
            STUDENT_GROUP in groups
            or ADMIN_GROUP in groups
        )
    elif path == "/node":
        allowed = ADMIN_GROUP in groups
    else:
        return build_response(
            404,
            {
                "error": "Resource not found",
                "path": path,
            },
        )

    status_code = 200 if allowed else 403
    decision = "ALLOW" if allowed else "DENY"

    print(
        json.dumps(
            {
                "request_id": getattr(context, "aws_request_id", "unknown"),
                "path": path,
                "authenticated_user": authenticated_user,
                "groups": groups,
                "rbac_decision": decision,
            }
        )
    )

    if not allowed:
        return build_response(
            403,
            {
                "error": "Access denied",
                "path": path,
                "required_role": (
                    ADMIN_GROUP
                    if path == "/node"
                    else f"{STUDENT_GROUP} or {ADMIN_GROUP}"
                ),
            },
        )

    return build_response(
        200,
        {
            "message": "Access granted from Python",
            "path": path,
            "authenticated_user": authenticated_user,
            "groups": groups,
        },
    )
