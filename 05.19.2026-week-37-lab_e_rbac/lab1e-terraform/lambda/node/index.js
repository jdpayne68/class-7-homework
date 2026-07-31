const studentGroup = process.env.STUDENT_GROUP_NAME || "students";
const adminGroup = process.env.ADMIN_GROUP_NAME || "admins";

function normalizeGroups(value) {
  if (Array.isArray(value)) {
    return value
      .map((group) => String(group).trim())
      .filter(Boolean);
  }

  if (typeof value !== "string" || !value.trim()) {
    return [];
  }

  const trimmed = value.trim();

  try {
    const parsed = JSON.parse(trimmed);

    if (Array.isArray(parsed)) {
      return parsed
        .map((group) => String(group).trim())
        .filter(Boolean);
    }
  } catch {
    // Fall through to comma-separated parsing.
  }

  return trimmed
    .replace(/^\[/, "")
    .replace(/\]$/, "")
    .split(",")
    .map((group) => group.trim().replace(/^['"]|['"]$/g, ""))
    .filter(Boolean);
}

function buildResponse(statusCode, body) {
  return {
    statusCode,
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  };
}

exports.handler = async (event, context) => {
  const claims = event.requestContext?.authorizer?.claims || {};
  const groups = normalizeGroups(claims["cognito:groups"]);
  const path = event.resource || event.path || "";

  const authenticatedUser =
    claims["cognito:username"] ||
    claims.username ||
    claims.sub ||
    "unknown";

  let allowed;

  if (path === "/python") {
    allowed =
      groups.includes(studentGroup) ||
      groups.includes(adminGroup);
  } else if (path === "/node") {
    allowed = groups.includes(adminGroup);
  } else {
    return buildResponse(404, {
      error: "Resource not found",
      path,
    });
  }

  const decision = allowed ? "ALLOW" : "DENY";

  console.log(
    JSON.stringify({
      requestId: context.awsRequestId,
      path,
      authenticatedUser,
      groups,
      rbacDecision: decision,
    }),
  );

  if (!allowed) {
    return buildResponse(403, {
      error: "Access denied",
      path,
      requiredRole:
        path === "/node"
          ? adminGroup
          : `${studentGroup} or ${adminGroup}`,
    });
  }

  return buildResponse(200, {
    message: "Access granted from Node",
    path,
    authenticatedUser,
    groups,
  });
};
