#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(
  cd "$(dirname "${BASH_SOURCE[0]}")/.." &&
  pwd
)"

REGION="$(
  terraform -chdir="$ROOT_DIR/terraform" output -raw aws_region
)"
FUNCTION_NAME="$(
  terraform -chdir="$ROOT_DIR/terraform" output -raw analyzer_lambda_name
)"
RESPONSE_PATH="/tmp/lab-h-analyzer-response.json"

aws lambda invoke   --region "$REGION"   --function-name "$FUNCTION_NAME"   --cli-binary-format raw-in-base64-out   --payload '{}'   "$RESPONSE_PATH"

echo
python3 -m json.tool "$RESPONSE_PATH"
