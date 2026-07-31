#!/usr/bin/env python3

import base64
import getpass
import hashlib
import json
import subprocess
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any
from urllib.parse import quote

import boto3
import qrcode
from botocore.exceptions import BotoCoreError, ClientError


ROOT_DIR = Path(__file__).resolve().parents[1]
TERRAFORM_DIR = ROOT_DIR / "terraform"


def terraform_output_raw(name: str) -> str:
    """Read one string output from Terraform state."""
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


def decode_jwt_payload(token: str) -> dict[str, Any]:
    """
    Decode a JWT payload for a local summary.

    API Gateway performs the real token validation.
    This function does not make authorization decisions.
    """
    parts = token.split(".")

    if len(parts) != 3:
        raise ValueError("Unexpected JWT format.")

    payload = parts[1]
    payload += "=" * (-len(payload) % 4)

    return json.loads(
        base64.urlsafe_b64decode(payload).decode("utf-8")
    )


def open_totp_qr_code(
    username: str,
    secret_code: str,
    issuer: str,
) -> Path:
    """Create a temporary TOTP QR code and open it in macOS Preview."""
    account_label = quote(f"{issuer}:{username}")
    encoded_issuer = quote(issuer)

    totp_uri = (
        f"otpauth://totp/{account_label}"
        f"?secret={secret_code}"
        f"&issuer={encoded_issuer}"
        f"&algorithm=SHA1"
        f"&digits=6"
        f"&period=30"
    )

    fingerprint = hashlib.sha256(
        secret_code.encode("utf-8")
    ).hexdigest()[:8]

    safe_username = "".join(
        character
        if character.isalnum() or character in "-_"
        else "_"
        for character in username
    )

    temporary_file = tempfile.NamedTemporaryFile(
        prefix=f"lab-e-{safe_username}-{fingerprint}-",
        suffix=".png",
        delete=False,
    )

    qr_path = Path(temporary_file.name)
    temporary_file.close()

    image = qrcode.make(totp_uri)
    image.save(qr_path)

    subprocess.run(
        ["open", "-n", "-a", "Preview", str(qr_path)],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    print(f"QR account: {username}")
    print(f"QR fingerprint: {fingerprint}")

    return qr_path


def complete_totp_setup(
    client: Any,
    client_id: str,
    username: str,
    session: str,
    project_name: str,
) -> dict[str, Any]:
    """Associate and verify a software TOTP token."""
    association = client.associate_software_token(
        Session=session,
    )

    secret_code = association["SecretCode"]
    association_session = association["Session"]

    qr_path = open_totp_qr_code(
        username=username,
        secret_code=secret_code,
        issuer=project_name,
    )

    try:
        print(f"\nA Google Authenticator QR code opened for {username}.")
        print("Scan it, then return to this terminal.")
        print("Do not screenshot or share the QR code.")

        input("Press Enter after scanning the QR code: ")

        verification_code = input(
            f"Enter the current 6-digit code for {username}: "
        ).strip()

        verification = client.verify_software_token(
            Session=association_session,
            UserCode=verification_code,
            FriendlyDeviceName=f"{project_name}-{username}",
        )

        if verification.get("Status") != "SUCCESS":
            raise RuntimeError(
                f"TOTP verification failed for {username}."
            )

        print(f"TOTP enrollment succeeded for {username}.")

        return client.respond_to_auth_challenge(
            ClientId=client_id,
            ChallengeName="MFA_SETUP",
            Session=verification["Session"],
            ChallengeResponses={
                "USERNAME": username,
            },
        )

    finally:
        qr_path.unlink(missing_ok=True)


def respond_to_totp_challenge(
    client: Any,
    client_id: str,
    username: str,
    session: str,
) -> dict[str, Any]:
    """Respond when a user already has TOTP configured."""
    verification_code = input(
        f"Enter the current 6-digit code for {username}: "
    ).strip()

    return client.respond_to_auth_challenge(
        ClientId=client_id,
        ChallengeName="SOFTWARE_TOKEN_MFA",
        Session=session,
        ChallengeResponses={
            "USERNAME": username,
            "SOFTWARE_TOKEN_MFA_CODE": verification_code,
        },
    )


def authenticate_user(
    client: Any,
    client_id: str,
    username: str,
    password: str,
    project_name: str,
) -> dict[str, str]:
    """Authenticate one user and complete any required MFA challenge."""
    response = client.initiate_auth(
        ClientId=client_id,
        AuthFlow="USER_PASSWORD_AUTH",
        AuthParameters={
            "USERNAME": username,
            "PASSWORD": password,
        },
    )

    challenge_name = response.get("ChallengeName")

    if challenge_name == "MFA_SETUP":
        response = complete_totp_setup(
            client=client,
            client_id=client_id,
            username=username,
            session=response["Session"],
            project_name=project_name,
        )

    elif challenge_name == "SOFTWARE_TOKEN_MFA":
        response = respond_to_totp_challenge(
            client=client,
            client_id=client_id,
            username=username,
            session=response["Session"],
        )

    elif challenge_name:
        raise RuntimeError(
            f"Unsupported Cognito challenge for {username}: "
            f"{challenge_name}"
        )

    authentication_result = response.get("AuthenticationResult")

    if not authentication_result:
        raise RuntimeError(
            f"Cognito did not return tokens for {username}."
        )

    return {
        "id_token": authentication_result["IdToken"],
        "access_token": authentication_result["AccessToken"],
    }


def call_api(
    url: str,
    id_token: str | None = None,
) -> tuple[int, str]:
    """Call one API route and return its HTTP status and response body."""
    headers = {
        "Accept": "application/json",
    }

    if id_token:
        headers["Authorization"] = id_token

    request = urllib.request.Request(
        url=url,
        headers=headers,
        method="GET",
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return (
                response.status,
                response.read().decode("utf-8"),
            )

    except urllib.error.HTTPError as error:
        return (
            error.code,
            error.read().decode("utf-8"),
        )


def safe_token_summary(
    username: str,
    tokens: dict[str, str],
) -> None:
    """Display selected claims without printing either token."""
    payload = decode_jwt_payload(tokens["id_token"])

    groups = payload.get("cognito:groups", [])

    print(f"\nAuthentication succeeded for {username}")
    print(f"  Token type: {payload.get('token_use', 'unknown')}")
    print(
        "  Username:   "
        f"{payload.get('cognito:username', username)}"
    )
    print(f"  Groups:     {', '.join(groups) or 'none'}")
    print("  ID token obtained:     yes")
    print("  Access token obtained: yes")
    print("  Tokens written to disk: no")


def run_api_test(
    label: str,
    url: str,
    expected_status: int,
    id_token: str | None = None,
) -> bool:
    """Run one HTTP test and display a concise result."""
    actual_status, response_body = call_api(
        url=url,
        id_token=id_token,
    )

    passed = actual_status == expected_status
    result = "PASS" if passed else "FAIL"

    print(
        f"{result}: {label} "
        f"(expected={expected_status}, actual={actual_status})"
    )

    if not passed:
        print(f"      Response: {response_body}")

    return passed


def main() -> None:
    region = terraform_output_raw("aws_region")
    client_id = terraform_output_raw(
        "cognito_user_pool_client_id"
    )
    project_name = terraform_output_raw("project_name")
    python_url = terraform_output_raw("python_api_url")
    node_url = terraform_output_raw("node_api_url")

    student_username = (
        input("Student username [student-lab-user]: ").strip()
        or "student-lab-user"
    )

    admin_username = (
        input("Admin username [admin-lab-user]: ").strip()
        or "admin-lab-user"
    )

    print("\nPasswords will not appear while you type.")
    student_password = getpass.getpass("Student password: ")
    admin_password = getpass.getpass("Admin password: ")

    client = boto3.client(
        "cognito-idp",
        region_name=region,
    )

    student_tokens = authenticate_user(
        client=client,
        client_id=client_id,
        username=student_username,
        password=student_password,
        project_name=project_name,
    )

    safe_token_summary(
        username=student_username,
        tokens=student_tokens,
    )

    admin_tokens = authenticate_user(
        client=client,
        client_id=client_id,
        username=admin_username,
        password=admin_password,
        project_name=project_name,
    )

    safe_token_summary(
        username=admin_username,
        tokens=admin_tokens,
    )

    print("\nRBAC API TEST MATRIX")
    print("====================")

    results = [
        run_api_test(
            label="No token may not access Python",
            url=python_url,
            expected_status=401,
        ),
        run_api_test(
            label="Student may access Python",
            url=python_url,
            expected_status=200,
            id_token=student_tokens["id_token"],
        ),
        run_api_test(
            label="Student may not access Node",
            url=node_url,
            expected_status=403,
            id_token=student_tokens["id_token"],
        ),
        run_api_test(
            label="Admin may access Python",
            url=python_url,
            expected_status=200,
            id_token=admin_tokens["id_token"],
        ),
        run_api_test(
            label="Admin may access Node",
            url=node_url,
            expected_status=200,
            id_token=admin_tokens["id_token"],
        ),
    ]

    if not all(results):
        raise SystemExit("\nRBAC API testing failed.")

    print("\n==============================================")
    print("COGNITO AUTHENTICATION AND RBAC TESTING: PASS")
    print("All five expected API authorization results matched.")
    print("No passwords, MFA secrets, or tokens were written to disk.")
    print("==============================================")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as error:
        print("\nERROR: Unable to read Terraform outputs.")
        if error.stderr:
            print(error.stderr.strip())
        raise SystemExit(1) from error
    except (BotoCoreError, ClientError) as error:
        print(f"\nAWS Cognito operation failed: {error}")
        raise SystemExit(1) from error
    except (RuntimeError, ValueError) as error:
        print(f"\nAuthentication or test failure: {error}")
        raise SystemExit(1) from error
