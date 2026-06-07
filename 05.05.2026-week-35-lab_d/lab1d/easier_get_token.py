# IMPORTANT unless you want Lizzo hell
# App Client MUST NOT have a client secret enabled


import boto3
import getpass
import json

# =========================
# Configuration
# =========================

CLIENT_ID = "2qgjjg59s5amsc39tmbklffl9m"
REGION = "us-west-2"

# =========================
# User Input
# =========================

username = input("Username: ")
password = getpass.getpass("Password: ")

# =========================
# Cognito Client
# =========================

client = boto3.client("cognito-idp", region_name=REGION)

try:
    response = client.initiate_auth(
        ClientId=CLIENT_ID,
        AuthFlow="USER_PASSWORD_AUTH",
        AuthParameters={
            "USERNAME": username,
            "PASSWORD": password
        }
    )

    # =========================
    # Handle MFA Challenge
    # =========================

    if response.get("ChallengeName") in ["SMS_MFA", "SOFTWARE_TOKEN_MFA"]:
        challenge_name = response["ChallengeName"]
        code = input("Enter MFA Code: ")

        if challenge_name == "SMS_MFA":
            code_key = "SMS_MFA_CODE"
        else:
            code_key = "SOFTWARE_TOKEN_MFA_CODE"

        response = client.respond_to_auth_challenge(
            ClientId=CLIENT_ID,
            ChallengeName=challenge_name,
            Session=response["Session"],
            ChallengeResponses={
                "USERNAME": username,
                code_key: code
            }
        )

    # =========================
    # Extract Tokens
    # =========================

    auth = response["AuthenticationResult"]

    print("\n========== TOKENS ==========\n")

    print("Access Token:\n")
    print(auth["AccessToken"])

    print("\n============================\n")

except Exception as e:
    print("\nAuthentication Failed\n")
    print(str(e))