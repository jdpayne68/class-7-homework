#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(
  cd "$(dirname "${BASH_SOURCE[0]}")/.." &&
  pwd
)"

API_URL="$(
  terraform -chdir="$ROOT_DIR/terraform" output -raw api_analyze_url
)"

echo "WAF BLOCK TEST"
echo "=============="

HTTP_STATUS="$(
  curl     --silent     --show-error     --output /tmp/lab-h-waf-response.txt     --write-out '%{http_code}'     --get     --data-urlencode 'name=<script>alert(1)</script>'     "$API_URL"
)"

echo "HTTP status: $HTTP_STATUS"
echo "Response body:"
cat /tmp/lab-h-waf-response.txt
echo

if [[ "$HTTP_STATUS" != "403" ]]; then
  echo "FAIL: expected AWS WAF to return HTTP 403." >&2
  exit 1
fi

echo "PASS: AWS WAF blocked the suspicious request."
echo "Waiting 15 seconds for WAF log delivery..."
sleep 15
