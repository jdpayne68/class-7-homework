data "archive_file" "python" {
  type        = "zip"
  source_file = "${path.module}/../lambda/python/lambda_function.py"
  output_path = "${path.module}/../lambda/python/python-lambda.zip"
}

data "archive_file" "node" {
  type        = "zip"
  source_file = "${path.module}/../lambda/node/index.js"
  output_path = "${path.module}/../lambda/node/node-lambda.zip"
}

resource "aws_lambda_function" "python" {
  function_name = local.python_function_name
  description   = "Python RBAC endpoint for Lab E."

  role    = aws_iam_role.lambda_execution.arn
  runtime = "python3.12"
  handler = "lambda_function.lambda_handler"

  filename         = data.archive_file.python.output_path
  source_code_hash = data.archive_file.python.output_base64sha256

  architectures = ["x86_64"]
  memory_size   = 128
  timeout       = 10

  environment {
    variables = {
      STUDENT_GROUP_NAME = var.student_group_name
      ADMIN_GROUP_NAME   = var.admin_group_name
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic_execution,
    aws_cloudwatch_log_group.python_lambda,
  ]
}

resource "aws_lambda_function" "node" {
  function_name = local.node_function_name
  description   = "Node.js RBAC endpoint for Lab E."

  role    = aws_iam_role.lambda_execution.arn
  runtime = "nodejs24.x"
  handler = "index.handler"

  filename         = data.archive_file.node.output_path
  source_code_hash = data.archive_file.node.output_base64sha256

  architectures = ["x86_64"]
  memory_size   = 128
  timeout       = 10

  environment {
    variables = {
      STUDENT_GROUP_NAME = var.student_group_name
      ADMIN_GROUP_NAME   = var.admin_group_name
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic_execution,
    aws_cloudwatch_log_group.node_lambda,
  ]
}
