#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(
  cd "$(dirname "${BASH_SOURCE[0]}")/.." &&
  pwd
)"

TF_DIR="$ROOT_DIR/terraform"

cd "$ROOT_DIR"

echo "==> Initializing Terraform without a remote backend"
terraform -chdir="$TF_DIR" init \
  -backend=false \
  -input=false \
  >/dev/null

echo "==> Checking Terraform formatting"
terraform -chdir="$TF_DIR" fmt -check -recursive

echo "==> Validating Terraform"
terraform -chdir="$TF_DIR" validate

echo "==> Checking Python syntax"
python3 -m py_compile \
  lambda/python/lambda_function.py \
  scripts/create_test_users.py \
  scripts/authenticate_and_test.py \
  scripts/test_python_rbac.py

echo "==> Checking Node.js syntax"
node --check lambda/node/index.js
node --check scripts/test_node_rbac.js

echo "==> Running Python RBAC tests"
python3 scripts/test_python_rbac.py

echo "==> Running Node RBAC tests"
node scripts/test_node_rbac.js

echo "==> Confirming generated and sensitive files are ignored"

ignored_paths=(
  "terraform/terraform.tfstate"
  "terraform/tfplan"
  "terraform/tfplan.outputs"
  "terraform/tfplan.destroy"
  "lambda/python/python-lambda.zip"
  "lambda/node/node-lambda.zip"
  ".venv/pyvenv.cfg"
  "auth.json"
)

for path in "${ignored_paths[@]}"; do
  if git check-ignore -q --no-index "$path"; then
    echo "PASS: ignored: $path"
  else
    echo "FAIL: not ignored: $path" >&2
    exit 1
  fi
done

echo
echo "=============================================="
echo "LAB E STATIC VALIDATION: PASS"
echo "Terraform, Lambda code, RBAC tests, and Git protections passed."
echo "=============================================="
