#!/usr/bin/env python3

import getpass
import json
import subprocess
from pathlib import Path
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError


ROOT_DIR = Path(__file__).resolve().parents[1]
TERRAFORM_DIR = ROOT_DIR / "terraform"


def terraform_output_raw(name: str) -> str:
    """Read one string value from Terraform state."""
    result = subprocess.run(
        [
            "terraform",
            f"-chdir={TERRAFORM_DIR}",
            "output",
            "-raw",
            name,
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    return result.stdout.strip()


def terraform_output_json(name: str) -> Any:
    """Read one structured Terraform output as JSON."""
    result = subprocess.run(
        [
            "terraform",
            f"-chdir={TERRAFORM_DIR}",
            "output",
            "-json",
            name,
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    return json.loads(result.stdout)


def password_is_valid(password: str) -> bool:
    """Check the password against this lab's Cognito policy."""
    return all(
        [
            len(password) >= 12,
            any(character.islower() for character in password),
            any(character.isupper() for character in password),
            any(character.isdigit() for character in password),
            any(not character.isalnum() for character in password),
            not any(character.isspace() for character in password),
        ]
    )


def prompt_for_password(label: str) -> str:
    """Prompt twice without displaying or storing the password."""
    while True:
        password = getpass.getpass(f"{label} password: ")
        confirmation = getpass.getpass(f"Confirm {label} password: ")

        if password != confirmation:
            print("Passwords did not match. Try again.\n")
            continue

        if not password_is_valid(password):
            print(
                "Password must contain at least 12 characters, "
                "uppercase, lowercase, a number, and a symbol, "
                "with no spaces.\n"
            )
            continue

        return password


def create_or_update_user(
    client: Any,
    user_pool_id: str,
    username: str,
    password: str,
    group_name: str,
) -> None:
    """Create a Cognito test user and ensure correct group membership."""
    created = False

    try:
        client.admin_create_user(
            UserPoolId=user_pool_id,
            Username=username,
            TemporaryPassword=password,
            MessageAction="SUPPRESS",
        )
        created = True
    except client.exceptions.UsernameExistsException:
        print(f"INFO: User already exists: {username}")

    client.admin_set_user_password(
        UserPoolId=user_pool_id,
        Username=username,
        Password=password,
        Permanent=True,
    )

    client.admin_add_user_to_group(
        UserPoolId=user_pool_id,
        Username=username,
        GroupName=group_name,
    )

    user = client.admin_get_user(
        UserPoolId=user_pool_id,
        Username=username,
    )

    group_response = client.admin_list_groups_for_user(
        UserPoolId=user_pool_id,
        Username=username,
    )

    groups = sorted(
        group["GroupName"]
        for group in group_response.get("Groups", [])
    )

    action = "Created" if created else "Updated"

    print(f"\n{action} user successfully")
    print(f"  Username: {username}")
    print(f"  Status:   {user.get('UserStatus', 'UNKNOWN')}")
    print(f"  Enabled:  {user.get('Enabled', False)}")
    print(f"  Groups:   {', '.join(groups) or 'none'}")


def main() -> None:
    region = terraform_output_raw("aws_region")
    user_pool_id = terraform_output_raw("cognito_user_pool_id")
    groups = terraform_output_json("cognito_group_names")

    student_group = groups["students"]
    admin_group = groups["admins"]

    student_username = (
        input("Student username [student-lab-user]: ").strip()
        or "student-lab-user"
    )

    admin_username = (
        input("Admin username [admin-lab-user]: ").strip()
        or "admin-lab-user"
    )

    print("\nPasswords will not appear while you type.")
    print("Passwords will not be printed or written to disk.\n")

    student_password = prompt_for_password("Student")
    admin_password = prompt_for_password("Admin")

    client = boto3.client(
        "cognito-idp",
        region_name=region,
    )

    print("\nProvisioning Cognito users...")

    create_or_update_user(
        client=client,
        user_pool_id=user_pool_id,
        username=student_username,
        password=student_password,
        group_name=student_group,
    )

    create_or_update_user(
        client=client,
        user_pool_id=user_pool_id,
        username=admin_username,
        password=admin_password,
        group_name=admin_group,
    )

    print("\n==============================================")
    print("COGNITO USER PROVISIONING: PASS")
    print("Two users are confirmed and assigned to roles.")
    print("No passwords or tokens were written to disk.")
    print("==============================================")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as error:
        print("\nERROR: Unable to read the required Terraform outputs.")
        if error.stderr:
            print(error.stderr.strip())
        raise SystemExit(1) from error
    except (BotoCoreError, ClientError) as error:
        print(f"\nAWS Cognito operation failed: {error}")
        raise SystemExit(1) from error
