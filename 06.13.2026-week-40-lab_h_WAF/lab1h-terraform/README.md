# Lab H: WAF Telemetry, DynamoDB, and Bedrock Analysis

This project builds an AWS WAF security-analysis pipeline.

```text
Suspicious request
      |
      v
API Gateway REST API
      |
      v
AWS WAF managed rules
      |
      v
CloudWatch WAF logs
      |
      v
WAF analyzer Lambda
   |              |
   v              v
DynamoDB      Amazon Bedrock
```

The analyzer processes new blocked WAF events, stores normalized telemetry in DynamoDB, and requests a cautious SOC-style assessment from Claude Sonnet 4.6. Bedrock assists a human analyst and does not independently confirm compromise.

## Validate

```bash
chmod 700 scripts/*.sh
./scripts/validate.sh
```

Expected:

```text
LAB H STATIC VALIDATION: PASS
```

## Deploy

```bash
terraform -chdir=terraform init
terraform -chdir=terraform plan -out=tfplan
terraform -chdir=terraform apply tfplan
terraform -chdir=terraform output
```

## Test

```bash
./scripts/generate_waf_event.sh
./scripts/invoke_analyzer.sh

python scripts/show_analyzer_response.py   --response /tmp/lab-h-analyzer-response.json
```

## Evidence checklist

```text
01-terraform-apply-complete.png
02-api-and-waf-association.png
03-waf-blocked-request-403.png
04-waf-cloudwatch-event.png
05-analyzer-bedrock-response.png
06-dynamodb-waf-event.png
07-analyzer-cloudwatch-finding.png
08-eventbridge-schedule.png
09-bedrock-iam-policy.png
10-terraform-no-drift.png
11-terraform-destroy-complete.png
```

Redact account identifiers, source IP addresses, request identifiers, and event identifiers before publishing evidence.

## Cleanup

```bash
terraform -chdir=terraform plan -destroy -out=tfplan.destroy
terraform -chdir=terraform apply tfplan.destroy
terraform -chdir=terraform state list
terraform -chdir=terraform plan -destroy
rm -f terraform/tfplan*
```
