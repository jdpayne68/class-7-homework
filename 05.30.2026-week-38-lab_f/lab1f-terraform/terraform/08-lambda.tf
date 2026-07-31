data "archive_file" "protected_api" {
  type        = "zip"
  source_file = "${path.module}/../lambda/protected-api/lambda_function.py"
  output_path = "${path.module}/../lambda/protected-api/protected-api.zip"
}

resource "aws_lambda_function" "protected_api" {
  function_name = local.protected_lambda_name
  role          = aws_iam_role.protected_api.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.12"

  filename         = data.archive_file.protected_api.output_path
  source_code_hash = data.archive_file.protected_api.output_base64sha256

  timeout     = 15
  memory_size = 128

  environment {
    variables = {
      TOKEN_TABLE_NAME = aws_dynamodb_table.token_tracking.name
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.protected_api,
    aws_iam_role_policy_attachment.protected_basic,
    aws_iam_role_policy.protected_dynamodb,
  ]
}

data "archive_file" "detector" {
  type        = "zip"
  source_file = "${path.module}/../lambda/detector/lambda_function.py"
  output_path = "${path.module}/../lambda/detector/detector.zip"
}

resource "aws_lambda_function" "detector" {
  function_name = local.detector_lambda_name
  role          = aws_iam_role.detector.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.12"

  filename         = data.archive_file.detector.output_path
  source_code_hash = data.archive_file.detector.output_base64sha256

  timeout     = 30
  memory_size = 128

  environment {
    variables = {
      TOKEN_TABLE_NAME    = aws_dynamodb_table.token_tracking.name
      ALERT_AFTER_MINUTES = tostring(var.alert_after_minutes)
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.detector,
    aws_iam_role_policy_attachment.detector_basic,
    aws_iam_role_policy.detector_dynamodb,
  ]
}
