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
terraform -chdir="$TF_DIR" init \
  -backend=false \
  -input=false \
  >/dev/null

echo "==> Terraform validation"
terraform -chdir="$TF_DIR" validate

echo "==> Python syntax"
python3 -m py_compile \
  "$ROOT_DIR/lambda/detector/lambda_function.py" \
  "$ROOT_DIR/lambda/protected-api/lambda_function.py" \
  "$ROOT_DIR/scripts/create_test_user.py" \
  "$ROOT_DIR/scripts/authenticate_and_test.py" \
  "$ROOT_DIR/scripts/create_unused_test_token.py" \
  "$ROOT_DIR/scripts/show_detector_response.py" \
  "$ROOT_DIR/scripts/export_detector_report.py"

echo "==> Git ignore protections"
ignored_paths=(
  "terraform/terraform.tfstate"
  "terraform/tfplan"
  "terraform/tfplan.destroy"
  "terraform/.terraform/providers/example"
  ".venv/pyvenv.cfg"
  "lambda/detector/detector.zip"
  "lambda/protected-api/protected-api.zip"
  "auth.json"
)

cd "$ROOT_DIR"

for ignored_path in "${ignored_paths[@]}"; do
  if git check-ignore -q --no-index "$ignored_path"; then
    echo "PASS: ignored: $ignored_path"
  else
    echo "FAIL: not ignored: $ignored_path" >&2
    exit 1
  fi
done

echo
echo "=============================================="
echo "LAB G STATIC VALIDATION: PASS"
echo "=============================================="
