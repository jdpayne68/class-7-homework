data "archive_file" "api" {
  type        = "zip"
  source_file = "${path.module}/../lambda/api/lambda_function.py"
  output_path = "${path.module}/../lambda/api/api.zip"
}

resource "aws_lambda_function" "api" {
  function_name = local.api_lambda_name
  role          = aws_iam_role.api.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.12"

  filename         = data.archive_file.api.output_path
  source_code_hash = data.archive_file.api.output_base64sha256

  memory_size = 128
  timeout     = 10

  depends_on = [
    aws_cloudwatch_log_group.api,
    aws_iam_role_policy_attachment.api_basic,
  ]
}

data "archive_file" "analyzer" {
  type        = "zip"
  source_file = "${path.module}/../lambda/analyzer/lambda_function.py"
  output_path = "${path.module}/../lambda/analyzer/analyzer.zip"
}

resource "aws_lambda_function" "analyzer" {
  function_name = local.analyzer_lambda_name
  role          = aws_iam_role.analyzer.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.12"

  filename         = data.archive_file.analyzer.output_path
  source_code_hash = data.archive_file.analyzer.output_base64sha256

  memory_size = 256
  timeout     = 90

  environment {
    variables = {
      WAF_LOG_GROUP      = aws_cloudwatch_log_group.waf.name
      DYNAMODB_TABLE     = aws_dynamodb_table.waf_events.name
      BEDROCK_MODEL_ID   = var.bedrock_model_id
      LOOKBACK_MINUTES   = tostring(var.lookback_minutes)
      MAX_EVENTS         = tostring(var.max_events)
      BEDROCK_MAX_TOKENS = tostring(var.bedrock_max_tokens)
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.analyzer,
    aws_iam_role_policy_attachment.analyzer_basic,
    aws_iam_role_policy.analyzer_logs,
    aws_iam_role_policy.analyzer_dynamodb,
    aws_iam_role_policy.analyzer_bedrock,
  ]
}
