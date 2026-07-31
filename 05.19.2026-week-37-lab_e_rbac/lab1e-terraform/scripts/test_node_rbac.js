const path = require("path");

const lambdaPath = path.resolve(
  __dirname,
  "..",
  "lambda",
  "node",
  "index.js",
);

const { handler } = require(lambdaPath);

const testCases = [
  {
    name: "Student may access Python",
    path: "/python",
    groups: ["students"],
    expectedStatus: 200,
  },
  {
    name: "Student may not access Node",
    path: "/node",
    groups: ["students"],
    expectedStatus: 403,
  },
  {
    name: "Admin may access Python",
    path: "/python",
    groups: ["admins"],
    expectedStatus: 200,
  },
  {
    name: "Admin may access Node",
    path: "/node",
    groups: ["admins"],
    expectedStatus: 200,
  },
  {
    name: "Unknown group may not access Python",
    path: "/python",
    groups: ["unknown-group"],
    expectedStatus: 403,
  },
  {
    name: "User without groups may not access Python",
    path: "/python",
    groups: [],
    expectedStatus: 403,
  },
  {
    name: "Unknown resource returns not found",
    path: "/unknown",
    groups: ["admins"],
    expectedStatus: 404,
  },
];

function buildEvent(resourcePath, groups) {
  return {
    resource: resourcePath,
    requestContext: {
      authorizer: {
        claims: {
          "cognito:username": "local-test-user",
          "cognito:groups": groups,
        },
      },
    },
  };
}

async function runTests() {
  let failures = 0;

  console.log("Node RBAC tests");
  console.log("===============");

  for (const testCase of testCases) {
    const response = await handler(
      buildEvent(testCase.path, testCase.groups),
      {
        awsRequestId: "local-node-test",
      },
    );

    const actualStatus = response.statusCode;
    const passed = actualStatus === testCase.expectedStatus;
    const marker = passed ? "PASS" : "FAIL";

    console.log(
      `${marker}: ${testCase.name} ` +
        `(expected=${testCase.expectedStatus}, actual=${actualStatus})`,
    );

    if (!passed) {
      failures += 1;
      console.log(`      Response body: ${response.body}`);
    }
  }

  if (failures > 0) {
    console.error(`\nNode RBAC tests failed: ${failures}`);
    process.exit(1);
  }

  console.log(`\nAll ${testCases.length} Node RBAC tests passed.`);
}

runTests().catch((error) => {
  console.error("Unexpected Node test failure:");
  console.error(error);
  process.exit(1);
});
