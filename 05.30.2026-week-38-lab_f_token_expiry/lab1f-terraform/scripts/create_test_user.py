#!/usr/bin/env python3
from __future__ import annotations

import getpass
import json
import subprocess
import sys

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


def main() -> int:
    outputs = terraform_outputs()
    region = output_value(outputs, "aws_region")
    user_pool_id = output_value(outputs, "cognito_user_pool_id")

    username = input("Username: ").strip()
    if not username:
        print("Username is required.", file=sys.stderr)
        return 1

    password = getpass.getpass("Permanent password: ")
    confirmation = getpass.getpass("Confirm password: ")
    if password != confirmation:
        print("Passwords do not match.", file=sys.stderr)
        return 1

    client = boto3.client("cognito-idp", region_name=region)

    try:
        client.admin_create_user(
            UserPoolId=user_pool_id,
            Username=username,
            TemporaryPassword=password,
            MessageAction="SUPPRESS",
        )
    except client.exceptions.UsernameExistsException:
        print("User already exists; updating the permanent password.")

    try:
        client.admin_set_user_password(
            UserPoolId=user_pool_id,
            Username=username,
            Password=password,
            Permanent=True,
        )
    except ClientError as exc:
        print(f"Unable to set password: {exc}", file=sys.stderr)
        return 1

    print(f"PASS: Cognito user is ready: {username}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
