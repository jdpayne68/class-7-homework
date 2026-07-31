# Lab G: Bedrock-Enriched SOAR Workflow

This project extends Lab F's unused-token telemetry into an AI-assisted security orchestration, automation, and response workflow.

When a Cognito authentication token remains unused beyond ten minutes, a scheduled detector Lambda gathers the event details, invokes Amazon Bedrock through the US Claude Sonnet 4.6 inference profile, and records a cautious SOC-style analysis in CloudWatch Logs.

Amazon Bedrock assists the analyst with interpretation. It does not autonomously disable accounts or make final security decisions.

## Workflow

```text
Cognito authentication
        |
        v
DynamoDB token-tracking table
        |
        +-----------------------------+
        |                             |
        v                             v
Protected API                  EventBridge Scheduler
marks token used=true          every five minutes
                                      |
                                      v
                               Detector Lambda
                                      |
                                      v
                         Amazon Bedrock Converse API
                                      |
                                      v
                       AI-enriched CloudWatch finding
```

## AI enrichment output

For every stale unused token, the detector requests:

1. Severity with justification
2. Benign explanations
3. Suspicious explanations
4. Prioritized analyst actions
5. Executive summary
6. Recommended remediation controls

The prompt explicitly requires uncertainty to be stated and prohibits automatically disabling a user based on an unused-token event alone.

## Security controls

- Cognito application client without a client secret
- Cognito authorizer on the protected API
- DynamoDB token ownership check against the authenticated username
- Least-privilege DynamoDB permissions
- Bedrock invocation restricted to the configured inference profile
- Foundation-model access conditioned on that inference profile
- CloudWatch logging
- No passwords or authentication tokens written to disk
- Terraform state, plans, Lambda archives, caches, and virtual environments ignored by Git

## Validate

```bash
./scripts/validate.sh
```

Expected:

```text
LAB G STATIC VALIDATION: PASS
```

## Deploy

```bash
terraform -chdir=terraform init
terraform -chdir=terraform plan -out=tfplan
terraform -chdir=terraform apply tfplan
terraform -chdir=terraform output
```

## Test the token workflow

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r scripts/requirements.txt
python scripts/create_test_user.py
python scripts/authenticate_and_test.py
```

## Test AI enrichment

```bash
python scripts/create_unused_test_token.py

REGION="$(terraform -chdir=terraform output -raw aws_region)"
DETECTOR_NAME="$(terraform -chdir=terraform output -raw detector_lambda_name)"

aws lambda invoke \
  --region "$REGION" \
  --function-name "$DETECTOR_NAME" \
  --cli-binary-format raw-in-base64-out \
  --payload '{}' \
  /tmp/lab-g-detector-response.json

python -m json.tool /tmp/lab-g-detector-response.json
```

A successful response should show:

```text
finding_count: 1
ai_enrichments_succeeded: 1
ai_enrichments_failed: 0
ai_enrichment.status: SUCCESS
```

## Export the AI analysis as PDF

The saved Lambda response can be converted into a printable, paginated incident report:

```bash
python scripts/export_detector_report.py \
  --response /tmp/lab-g-detector-response.json \
  --output evidence/06-bedrock-enriched-detector-response.pdf
```

The exporter wraps long text, formats Markdown headings and lists, adds page numbers, and automatically redacts the token identifier.

To redact the username as well:

```bash
python scripts/export_detector_report.py \
  --response /tmp/lab-g-detector-response.json \
  --output evidence/06-bedrock-enriched-detector-response.pdf \
  --redact-username
```

## Evidence checklist

```text
01-terraform-apply-complete.png
02-bedrock-model-and-profile-access.png
03-dynamodb-table-configuration.png
04-token-telemetry-end-to-end.png
05-stale-unused-token-created.png
06-bedrock-enriched-detector-response.png
07-cloudwatch-ai-enriched-finding.png
08-eventbridge-schedule.png
09-bedrock-iam-policy.png
10-terraform-no-drift.png
11-terraform-destroy-complete.png
```

Redact account identifiers, request identifiers, usernames, and token identifiers before publishing screenshots publicly.

## Cleanup

```bash
terraform -chdir=terraform plan -destroy -out=tfplan.destroy
terraform -chdir=terraform apply tfplan.destroy
terraform -chdir=terraform state list
terraform -chdir=terraform plan -destroy
rm -f terraform/tfplan*
```
