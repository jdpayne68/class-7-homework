# Lab E: Cognito Role-Based Access Control

This project rebuilds the Lab E Cognito RBAC environment with Terraform.

It demonstrates authentication with Amazon Cognito, route-level authorization in AWS Lambda, API protection through API Gateway, TOTP multifactor authentication, AWS WAF protection, CloudWatch logging, and repeatable infrastructure cleanup.

## Architecture

The deployed request path is:

```text
Client
  |
  | Cognito ID token in Authorization header
  v
Amazon API Gateway
  |
  | Cognito user-pool authorizer
  v
AWS Lambda
  |
  | Evaluates the cognito:groups claim
  v
RBAC allow or deny response
```

Supporting services include:

- Amazon Cognito user pool
- Cognito groups for students and administrators
- Cognito application client without a client secret
- API Gateway REST API
- Python and Node.js Lambda functions
- AWS WAF regional web ACL
- Amazon CloudWatch log groups
- IAM execution role and logging permissions

## RBAC Access Matrix

| Cognito group | GET /python | GET /node |
|---|---:|---:|
| students | Allowed | Denied |
| admins | Allowed | Allowed |
| Unknown or missing group | Denied | Denied |

Both API routes require a valid Cognito token before Lambda evaluates group membership.

## Security Controls

The project implements the following controls:

- TOTP MFA is required by the Cognito user pool.
- Users are created administratively.
- Password policy requires at least 12 characters.
- The application client does not use a client secret.
- API Gateway reads the token from the `Authorization` header.
- Both API methods use a `COGNITO_USER_POOLS` authorizer.
- Lambda authorization uses default-deny logic.
- WAF uses the AWS managed common rule set.
- WAF includes request-rate protection.
- The `Authorization` header is redacted from WAF logs.
- Authentication tokens, passwords, TOTP secrets, and QR codes are not written to the repository.
- Terraform state, saved plans, Lambda archives, virtual environments, and local authentication files are ignored by Git.

## Project Structure

```text
.
├── evidence/
├── lambda/
│   ├── node/
│   │   └── index.js
│   └── python/
│       └── lambda_function.py
├── scripts/
│   ├── authenticate_and_test.py
│   ├── create_test_users.py
│   ├── requirements.txt
│   ├── test_node_rbac.js
│   ├── test_python_rbac.py
│   └── validate.sh
└── terraform/
    ├── 00-versions.tf
    ├── 01-provider.tf
    ├── 02-data.tf
    ├── 03-variables.tf
    ├── 04-locals.tf
    ├── 05-iam.tf
    ├── 06-cognito.tf
    ├── 07-cloudwatch.tf
    ├── 08-lambda.tf
    ├── 09-api-gateway.tf
    ├── 10-waf.tf
    └── 11-outputs.tf
```

## Prerequisites

- Terraform
- AWS CLI
- Python 3
- Node.js
- AWS credentials with permission to manage the required services
- An authenticator application that supports TOTP

Verify the active AWS identity before deployment:

```bash
aws sts get-caller-identity
```

## Python Environment

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r scripts/requirements.txt
```

The `.venv` directory is excluded from Git.

## Static Validation

Run the complete local validation suite:

```bash
./scripts/validate.sh
```

The validator checks:

- Terraform formatting
- Terraform configuration validity
- Python syntax
- Node.js syntax
- Python RBAC tests
- Node.js RBAC tests
- Git ignore protections for generated and sensitive files

Expected final result:

```text
LAB E STATIC VALIDATION: PASS
```

## Deployment

Initialize Terraform:

```bash
terraform -chdir=terraform init
```

Review the deployment plan:

```bash
terraform -chdir=terraform plan
```

Deploy the infrastructure:

```bash
terraform -chdir=terraform apply
```

Review Terraform outputs:

```bash
terraform -chdir=terraform output
```

## Test Users and MFA

The user-provisioning script creates the lab users, assigns their groups, and guides TOTP enrollment:

```bash
python scripts/create_test_users.py
```

Temporary TOTP QR-code files are removed after enrollment. Never commit QR codes, TOTP setup secrets, passwords, access tokens, ID tokens, refresh tokens, or MFA codes.

## Authentication and RBAC Testing

Run the interactive authentication and route test:

```bash
python scripts/authenticate_and_test.py
```

Expected authorization behavior:

```text
No token:       /python denied
Student token:  /python allowed
Student token:  /node denied
Admin token:    /python allowed
Admin token:    /node allowed
```

The test should end with:

```text
COGNITO AUTHENTICATION AND RBAC TESTING: PASS
```

## WAF Validation

An XSS-style query request should be blocked by AWS WAF with HTTP status `403`.

The corresponding WAF log should identify the managed common rule set and the cross-site-scripting query-argument rule as the blocking control.

Do not include authorization headers, tokens, passwords, client IP addresses, TOTP values, or other sensitive values in published evidence.

## Evidence

The `evidence` directory contains screenshots demonstrating:

- Successful Terraform deployment
- Cognito users and group membership
- Student and administrator authentication
- Complete RBAC result matrix
- WAF XSS blocking
- WAF CloudWatch logging
- Python Lambda RBAC logging
- Node.js Lambda allow and deny logging
- Required TOTP MFA configuration
- User-level MFA preferences
- Application-client security configuration
- API Gateway Cognito authorizer
- Protected API Gateway methods
- Terraform no-drift validation
- Successful Terraform destruction

Evidence is intended for private coursework review. Redact screenshots before public publication if they display account identifiers, request identifiers, usernames, email addresses, or other environment-specific information.

## Drift Check

After deployment, verify that the live environment matches the Terraform configuration:

```bash
terraform -chdir=terraform plan
```

Expected:

```text
No changes. Your infrastructure matches the configuration.
```

## Cleanup

Create and review a destroy plan:

```bash
terraform -chdir=terraform plan \
  -destroy \
  -out=tfplan.destroy
```

Apply the reviewed plan:

```bash
terraform -chdir=terraform apply tfplan.destroy
```

Verify that no Terraform-managed resources remain:

```bash
terraform -chdir=terraform state list
terraform -chdir=terraform plan -destroy
```

The state-list command should produce no resource output, and the destroy plan should report:

```text
No changes. No objects need to be destroyed.
```

Remove obsolete saved plans:

```bash
rm -f terraform/tfplan*
```

## Scope Note

The core lab intentionally uses a Cognito application client without a client secret. This avoids storing or calculating a secret hash in the main authentication workflow.

A client-secret and `SECRET_HASH` implementation should be treated as a separate optional exercise and must not introduce secrets into source control.
