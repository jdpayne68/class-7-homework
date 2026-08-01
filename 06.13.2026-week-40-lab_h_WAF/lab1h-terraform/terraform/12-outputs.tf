output "aws_region" {
  value = var.aws_region
}

output "api_analyze_url" {
  value = "${aws_api_gateway_stage.prod.invoke_url}/analyze"
}

output "api_lambda_name" {
  value = aws_lambda_function.api.function_name
}

output "analyzer_lambda_name" {
  value = aws_lambda_function.analyzer.function_name
}

output "analyzer_log_group_name" {
  value = aws_cloudwatch_log_group.analyzer.name
}

output "waf_log_group_name" {
  value = aws_cloudwatch_log_group.waf.name
}

output "waf_web_acl_name" {
  value = aws_wafv2_web_acl.api.name
}

output "waf_web_acl_arn" {
  value = aws_wafv2_web_acl.api.arn
}

output "waf_events_table_name" {
  value = aws_dynamodb_table.waf_events.name
}

output "eventbridge_schedule_name" {
  value = aws_scheduler_schedule.analyzer.name
}

output "bedrock_model_id" {
  value = var.bedrock_model_id
}

output "bedrock_inference_profile_arn" {
  value = local.bedrock_inference_profile_arn
}
