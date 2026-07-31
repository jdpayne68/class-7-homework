#!/usr/bin/env python3
from __future__ import annotations

import getpass
import json
import subprocess
import sys
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError


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


def authenticate(client, client_id: str, username: str, password: str) -> dict[str, str]:
    response = client.initiate_auth(
        ClientId=client_id,
        AuthFlow="USER_PASSWORD_AUTH",
        AuthParameters={"USERNAME": username, "PASSWORD": password},
    )
    challenge = response.get("ChallengeName")
    if challenge:
        raise RuntimeError(f"Unexpected Cognito challenge: {challenge}")
    return response["AuthenticationResult"]


def call_api(api_url: str, id_token: str, token_id: str) -> tuple[int, str]:
    request = urllib.request.Request(
        api_url,
        method="GET",
        headers={"Authorization": id_token, "x-token-id": token_id},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8")


def main() -> int:
    outputs = terraform_outputs()
    region = output_value(outputs, "aws_region")
    client_id = output_value(outputs, "cognito_app_client_id")
    table_name = output_value(outputs, "token_table_name")
    api_url = output_value(outputs, "protected_api_url")

    username = input("Username: ").strip()
    password = getpass.getpass("Password: ")

    cognito = boto3.client("cognito-idp", region_name=region)
    table = boto3.resource("dynamodb", region_name=region).Table(table_name)

    try:
        auth = authenticate(cognito, client_id, username, password)
    except (ClientError, RuntimeError) as exc:
        print(f"Authentication failed: {exc}", file=sys.stderr)
        return 1

    token_id = str(uuid.uuid4())
    issued_at = datetime.now(timezone.utc).isoformat()

    table.put_item(
        Item={
            "token_id": token_id,
            "username": username,
            "issued_at": issued_at,
            "used": False,
        }
    )

    print(f"PASS: authentication succeeded for {username}")
    print("PASS: token record created with used=false")
    print(f"Token ID: {token_id}")

    before = table.get_item(Key={"token_id": token_id}).get("Item", {})
    print("Before API request:")
    print(json.dumps(before, indent=2, default=str))

    status, body = call_api(api_url, auth["IdToken"], token_id)
    print(f"Protected API status: {status}")
    print(body)

    after = table.get_item(
        Key={"token_id": token_id},
        ConsistentRead=True,
    ).get("Item", {})

    print("After API request:")
    print(json.dumps(after, indent=2, default=str))

    if status != 200:
        print("FAIL: protected API did not return HTTP 200", file=sys.stderr)
        return 1
    if after.get("used") is not True:
        print("FAIL: token record was not marked used", file=sys.stderr)
        return 1

    print("TOKEN TELEMETRY TEST: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
