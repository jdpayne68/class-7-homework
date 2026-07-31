output "aws_region" {
  value = var.aws_region
}

output "token_table_name" {
  value = aws_dynamodb_table.token_tracking.name
}

output "cognito_user_pool_id" {
  value = aws_cognito_user_pool.lab.id
}

output "cognito_app_client_id" {
  value = aws_cognito_user_pool_client.lab.id
}

output "protected_api_url" {
  value = "${aws_api_gateway_stage.prod.invoke_url}/protected"
}

output "protected_lambda_name" {
  value = aws_lambda_function.protected_api.function_name
}

output "detector_lambda_name" {
  value = aws_lambda_function.detector.function_name
}

output "detector_log_group" {
  value = aws_cloudwatch_log_group.detector.name
}

output "eventbridge_schedule_name" {
  value = aws_scheduler_schedule.unused_token_check.name
}
