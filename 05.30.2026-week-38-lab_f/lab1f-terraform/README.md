# Lab F: Unused Cognito Token Detection

This project implements token-use telemetry for a Cognito-protected API.

After successful Cognito authentication, a local client records a token identifier in DynamoDB with `used = false`. A protected Lambda marks the record as used when the API receives the matching `x-token-id` header. A scheduled detector Lambda scans for tokens that remain unused longer than ten minutes and writes alerts to CloudWatch Logs.

## Architecture

```text
Cognito authentication
        |
        v
DynamoDB token-tracking table
  token_id, username, issued_at, used=false
        |
        +--------------------------+
        |                          |
        v                          v
Protected API request        EventBridge Scheduler
Authorization + x-token-id        every 5 minutes
        |                          |
        v                          v
Protected Lambda             Detector Lambda
marks used=true              logs stale unused tokens
```

## Required behavior

| Scenario | Expected result |
|---|---|
| Successful authentication | Token record created with `used = false` |
| Valid protected request with matching `x-token-id` | Record changes to `used = true` |
| Token remains unused for more than 10 minutes | Detector logs an alert |
| Missing or mismatched token ID | Request denied or rejected |

## Project structure

```text
lab1f-terraform/
├── evidence/
├── lambda/
│   ├── detector/
│   │   └── lambda_function.py
│   └── protected-api/
│       └── lambda_function.py
├── scripts/
│   ├── authenticate_and_test.py
│   ├── create_test_user.py
│   ├── create_unused_test_token.py
│   ├── requirements.txt
│   └── validate.sh
└── terraform/
    ├── .terraform.lock.hcl
    ├── 00-versions.tf
    ├── 01-provider.tf
    ├── 02-variables.tf
    ├── 03-locals.tf
    ├── 04-dynamodb.tf
    ├── 05-cognito.tf
    ├── 06-cloudwatch.tf
    ├── 07-iam.tf
    ├── 08-lambda.tf
    ├── 09-api-gateway.tf
    ├── 10-scheduler.tf
    └── 11-outputs.tf
```

## AWS services

- Amazon Cognito user pool and no-secret application client
- Amazon DynamoDB on-demand table
- Amazon API Gateway REST API with Cognito authorization
- AWS Lambda protected API and detector functions
- Amazon EventBridge Scheduler
- Amazon CloudWatch Logs
- AWS IAM roles and least-privilege policies

## Prerequisites

- AWS CLI authenticated to the intended account
- Terraform
- Python 3.11 or later

Verify the active identity before deployment:

```bash
aws sts get-caller-identity
```

## Local validation

```bash
./scripts/validate.sh
```

The validator checks Terraform formatting and validity, Python syntax, and Git protections for generated and sensitive files.

Expected final result:

```text
LAB F STATIC VALIDATION: PASS
```

## Deployment

```bash
terraform -chdir=terraform init
terraform -chdir=terraform plan -out=tfplan
terraform -chdir=terraform apply tfplan
terraform -chdir=terraform output
```

## Create a test user

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r scripts/requirements.txt
python scripts/create_test_user.py
```

Use a lab-only password that satisfies the Cognito password policy. Passwords must never be committed or pasted into documentation.

## End-to-end token telemetry test

```bash
python scripts/authenticate_and_test.py
```

The script authenticates through Cognito, creates a DynamoDB record with `used = false`, calls the protected API using the Cognito ID token and `x-token-id`, and confirms that the same DynamoDB record changed to `used = true`.

Expected final result:

```text
Protected API status: 200
TOKEN TELEMETRY TEST: PASS
```

Tokens and passwords remain in process memory and are not written to disk.

## Unused-token detection test

Create a token record older than the configured ten-minute threshold:

```bash
python scripts/create_unused_test_token.py
```

Invoke the detector immediately:

```bash
REGION="$(terraform -chdir=terraform output -raw aws_region)"
DETECTOR_NAME="$(terraform -chdir=terraform output -raw detector_lambda_name)"

aws lambda invoke \
  --region "$REGION" \
  --function-name "$DETECTOR_NAME" \
  --cli-binary-format raw-in-base64-out \
  --payload '{}' \
  /tmp/lab-f-detector-response.json

python -m json.tool /tmp/lab-f-detector-response.json
```

A successful response includes `alert_count: 1` and `alert_type: UNUSED_TOKEN`.

Inspect the detector logs:

```bash
LOG_GROUP="$(terraform -chdir=terraform output -raw detector_log_group)"

aws logs tail "$LOG_GROUP" \
  --region "$REGION" \
  --since 30m \
  --format short
```

## Scheduled detection

The EventBridge Scheduler runs the detector every five minutes:

```bash
SCHEDULE_NAME="$(terraform -chdir=terraform output -raw eventbridge_schedule_name)"

aws scheduler get-schedule \
  --region "$REGION" \
  --name "$SCHEDULE_NAME" \
  --query '{
    Name:Name,
    State:State,
    ScheduleExpression:ScheduleExpression,
    Timezone:ScheduleExpressionTimezone,
    FlexibleWindow:FlexibleTimeWindow.Mode,
    TargetLambda:Target.Arn
  }' \
  --output table
```

Expected configuration:

```text
Name: unused-token-check
State: ENABLED
ScheduleExpression: rate(5 minutes)
Timezone: UTC
FlexibleWindow: OFF
```

## Evidence

The `evidence` directory contains:

```text
01-terraform-apply-complete.png
02-dynamodb-table-configuration.png
03-token-telemetry-end-to-end.png
04-stale-unused-token-created.png
05-detector-lambda-response.png
06-cloudwatch-unused-token-alert.png
07-eventbridge-schedule.png
08-terraform-no-drift.png
09-terraform-destroy-complete.png
```

Together, these screenshots prove deployment, DynamoDB configuration, successful token-use telemetry, stale-token creation, detector execution, CloudWatch alerting, scheduled invocation, drift-free infrastructure, and cleanup.

Evidence is intended for private coursework review. Redact account numbers, usernames, request identifiers, and environment-specific values before publishing screenshots publicly.

## Drift check

```bash
terraform -chdir=terraform plan
```

Expected:

```text
No changes. Your infrastructure matches the configuration.
```

## Cleanup

```bash
terraform -chdir=terraform plan -destroy -out=tfplan.destroy
terraform -chdir=terraform apply tfplan.destroy
terraform -chdir=terraform state list
terraform -chdir=terraform plan -destroy
rm -f terraform/tfplan*
```

After cleanup, `terraform state list` should produce no resource output and Terraform should report:

```text
No changes. No objects need to be destroyed.
```

## Security notes

- The Cognito application client has no client secret.
- The protected API requires a Cognito user-pool authorizer.
- The API does not trust `x-token-id` by itself. It checks the DynamoDB record against the authenticated Cognito username.
- IAM permissions are scoped to the required DynamoDB table and Lambda functions.
- Passwords, ID tokens, access tokens, refresh tokens, and generated token identifiers are not committed.
- Terraform state, saved plans, deployment archives, and virtual environments are ignored by Git.
