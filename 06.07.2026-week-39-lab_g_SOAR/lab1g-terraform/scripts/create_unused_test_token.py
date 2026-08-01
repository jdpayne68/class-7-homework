#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import uuid
from datetime import datetime, timedelta, timezone

import boto3


def terraform_outputs() -> dict[str, dict[str, object]]:
    result = subprocess.run(
        ["terraform", "-chdir=terraform", "output", "-json"],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def output_value(outputs: dict[str, dict[str, object]], name: str) -> str:
    return str(outputs[name]["value"])


def main() -> int:
    outputs = terraform_outputs()
    region = output_value(outputs, "aws_region")
    table_name = output_value(outputs, "token_table_name")

    username = input("Username for unused-token test [unused-test-user]: ").strip()
    username = username or "unused-test-user"

    token_id = str(uuid.uuid4())
    issued_at = (datetime.now(timezone.utc) - timedelta(minutes=15)).isoformat()
    item = {
        "token_id": token_id,
        "username": username,
        "issued_at": issued_at,
        "used": False,
    }

    table = boto3.resource("dynamodb", region_name=region).Table(table_name)
    table.put_item(Item=item)

    print("PASS: stale unused-token test record created")
    print(json.dumps(item, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
