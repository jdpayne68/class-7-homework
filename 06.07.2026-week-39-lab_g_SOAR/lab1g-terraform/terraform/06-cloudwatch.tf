resource "aws_cloudwatch_log_group" "protected_api" {
  name              = "/aws/lambda/${local.protected_lambda_name}"
  retention_in_days = 7
}

resource "aws_cloudwatch_log_group" "detector" {
  name              = "/aws/lambda/${local.detector_lambda_name}"
  retention_in_days = 7
}
