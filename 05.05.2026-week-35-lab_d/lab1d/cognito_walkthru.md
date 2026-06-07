Cognito ClickOps Lab — User Authentication (No Federation)
We will do Federation in SEIR-II

Objective---> “We are not building a login page. We are building an identity system that issues tokens.”

Students will:

    Create a User Pool
    Enable login with:
        username
        email
        phone number
    Enforce MFA
    Create and authenticate a user
    Use the JWT to call your REST API

Updated Flow: Client → WAF → API Gateway (Cognito Authorizer) → Lambda


Task 1 — Create Cognito User Pool
  Navigation
  
    AWS Console → Cognito
    Click User Pools
    Click Create user pool


Step-by-Step Configuration


1. Sign-in Options

Select: “We allow multiple identity inputs. Real systems don’t force one.”

        ✔ Username
        ✔ Email
        ✔ Phone number

2. Password Policy

Keep default or slightly stronger:

        Min 8 characters
        Numbers + symbols

3. MFA Configuration---> “MFA is not optional in real systems.”

Set: Required MFA

        MFA Types:
        ✔ SMS
        ✔ TOTP (Authenticator app)

4. User Account Recovery

        Enable:
        ✔ Email
        ✔ Phone

5. Attributes

Set required:

        ✔ email
        ✔ phone_number

6. App Client

Create one:

Name: chewbacca-client

Disable: ----> ❌ Client secret

Why? Client secret complicates API usage. We keep it simple.

Click Create

Task 2 — Create a User

Inside User Pool:

        Go to Users
        Click Create user

Fill:

        Username: lizzo1
        Email: student1@lizzo.com
        Phone: +1XXXXXXXXXX

Set password manually: --->  Permanent password
“We are skipping email verification to move faster. We will return to it later"

Task 3 — Enable MFA for User

Inside User:
        Click user
        Set MFA:

        ✔ Enable MFA
        ✔ Choose:

SMS OR Authenticator app

If TOTP:
    Scan QR code with:
        Google Authenticator
        or Microsoft Authenticator


Task 4 — Get JWT Token (CLI Method)
This isn't easy. Let's go slow.

Use AWS CLI:

        aws cognito-idp initiate-auth \
          --auth-flow USER_PASSWORD_AUTH \
          --client-id <CLIENT_ID> \
          --auth-parameters USERNAME=student1,PASSWORD=YourPassword

If MFA is required → challenge returned

Then run:

        aws cognito-idp respond-to-auth-challenge \
          --client-id <CLIENT_ID> \
          --challenge-name SMS_MFA \
          --challenge-responses USERNAME=student1,SMS_MFA_CODE=123456 \
          --session <SESSION>

Result:

You get:

        {
          "AuthenticationResult": {
            "IdToken": "...",
            "AccessToken": "...",
            "RefreshToken": "..."
          }
        }

Use: AccessToken

Task 5 — Create API Gateway Authorizer

Go to API Gateway (REST API)--> Authorizers → Create New ---> Type: Cognito ---> 

Configure:

        Name:chewbacca-authorizer
        Cognito User Pool: → Select your pool
        Token Source: Authorization

Task 6 — Attach Authorizer to Methods

For /python and For /node:

    Method Request --> Authorization: Cognito Authorizer
 
Task 7 — Deploy API (Again!)

👉 REST API requires redeploy
Actions → Deploy API → prod

Task 8 — Test

Without Token ---> 

        curl https://<api>/prod/python 

 --> 401 Unauthorized
 

With Token -->  

        curl https://<api>/prod/python \
          -H "Authorization: <ACCESS_TOKEN>" 

→ 200 OK


Task 9 — Verify Behavior

1. Did Lambda run when no token?
2. Where was request blocked?
3. What changed in event?

Final Explanation

    What Cognito does?
    What API Gateway does?
    What MFA adds?
    Why AccessToken matters?