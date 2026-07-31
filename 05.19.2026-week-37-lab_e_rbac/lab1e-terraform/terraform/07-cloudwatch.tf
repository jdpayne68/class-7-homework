resource "aws_cloudwatch_log_group" "python_lambda" {
  name              = "/aws/lambda/${local.python_function_name}"
  retention_in_days = var.log_retention_days
}

resource "aws_cloudwatch_log_group" "node_lambda" {
  name              = "/aws/lambda/${local.node_function_name}"
  retention_in_days = var.log_retention_days
}
