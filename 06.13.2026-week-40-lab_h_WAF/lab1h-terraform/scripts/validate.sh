#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(
  cd "$(dirname "${BASH_SOURCE[0]}")/.." &&
  pwd
)"

TF_DIR="$ROOT_DIR/terraform"

echo "==> Terraform formatting"
terraform -chdir="$TF_DIR" fmt -check -recursive

echo "==> Terraform initialization"
terraform -chdir="$TF_DIR" init   -backend=false   -input=false   >/dev/null

echo "==> Terraform validation"
terraform -chdir="$TF_DIR" validate

echo "==> Python syntax"
python3 -m py_compile   "$ROOT_DIR/lambda/api/lambda_function.py"   "$ROOT_DIR/lambda/analyzer/lambda_function.py"   "$ROOT_DIR/scripts/show_analyzer_response.py"

echo "==> Bash syntax"
bash -n   "$ROOT_DIR/scripts/generate_waf_event.sh"   "$ROOT_DIR/scripts/invoke_analyzer.sh"   "$ROOT_DIR/scripts/validate.sh"

echo
echo "=============================================="
echo "LAB H STATIC VALIDATION: PASS"
echo "=============================================="
