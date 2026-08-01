resource "aws_cloudwatch_log_group" "api" {
  name              = "/aws/lambda/${local.api_lambda_name}"
  retention_in_days = 7
}

resource "aws_cloudwatch_log_group" "analyzer" {
  name              = "/aws/lambda/${local.analyzer_lambda_name}"
  retention_in_days = 7
}

resource "aws_cloudwatch_log_group" "waf" {
  name              = local.waf_log_group_name
  retention_in_days = 7
}
