import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any


LAMBDA_PATH = (
    Path(__file__).resolve().parents[1]
    / "lambda"
    / "python"
    / "lambda_function.py"
)

spec = importlib.util.spec_from_file_location(
    "python_rbac_lambda",
    LAMBDA_PATH,
)

if spec is None or spec.loader is None:
    raise RuntimeError(f"Unable to load Lambda module: {LAMBDA_PATH}")

module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


TEST_CASES = [
    {
        "name": "Student may access Python",
        "path": "/python",
        "groups": ["students"],
        "expected_status": 200,
    },
    {
        "name": "Student may not access Node",
        "path": "/node",
        "groups": ["students"],
        "expected_status": 403,
    },
    {
        "name": "Admin may access Python",
        "path": "/python",
        "groups": ["admins"],
        "expected_status": 200,
    },
    {
        "name": "Admin may access Node",
        "path": "/node",
        "groups": ["admins"],
        "expected_status": 200,
    },
    {
        "name": "Unknown group may not access Python",
        "path": "/python",
        "groups": ["unknown-group"],
        "expected_status": 403,
    },
    {
        "name": "User without groups may not access Python",
        "path": "/python",
        "groups": [],
        "expected_status": 403,
    },
    {
        "name": "Unknown resource returns not found",
        "path": "/unknown",
        "groups": ["admins"],
        "expected_status": 404,
    },
]


def build_event(path: str, groups: list[str]) -> dict[str, Any]:
    return {
        "resource": path,
        "requestContext": {
            "authorizer": {
                "claims": {
                    "cognito:username": "local-test-user",
                    "cognito:groups": groups,
                }
            }
        },
    }


failures = 0
context = SimpleNamespace(aws_request_id="local-python-test")

print("Python RBAC tests")
print("=================")

for test_case in TEST_CASES:
    response = module.lambda_handler(
        build_event(
            test_case["path"],
            test_case["groups"],
        ),
        context,
    )

    actual_status = response["statusCode"]
    response_body = json.loads(response["body"])
    passed = actual_status == test_case["expected_status"]

    marker = "PASS" if passed else "FAIL"

    print(
        f"{marker}: {test_case['name']} "
        f"(expected={test_case['expected_status']}, "
        f"actual={actual_status})"
    )

    if not passed:
        failures += 1
        print(f"      Response body: {response_body}")

if failures:
    raise SystemExit(f"\nPython RBAC tests failed: {failures}")

print(f"\nAll {len(TEST_CASES)} Python RBAC tests passed.")
