output "aws_account_id" {
  description = "AWS account in which Lab E is deployed."
  value       = data.aws_caller_identity.current.account_id
}

output "aws_region" {
  description = "AWS region containing the Lab E resources."
  value       = data.aws_region.current.region
}

output "project_name" {
  description = "Lab E project prefix."
  value       = var.project_name
}

output "cognito_user_pool_id" {
  description = "Cognito user pool ID."
  value       = aws_cognito_user_pool.main.id
}

output "cognito_user_pool_client_id" {
  description = "Cognito app client ID."
  value       = aws_cognito_user_pool_client.main.id
}

output "cognito_group_names" {
  description = "Cognito groups used for Lab E RBAC."

  value = {
    students = aws_cognito_user_group.students.name
    admins   = aws_cognito_user_group.admins.name
  }
}

output "cognito_authorizer_id" {
  description = "API Gateway Cognito authorizer ID."
  value       = aws_api_gateway_authorizer.cognito.id
}

output "api_base_url" {
  description = "Base URL for the deployed API Gateway stage."
  value       = aws_api_gateway_stage.prod.invoke_url
}

output "python_api_url" {
  description = "Protected Python endpoint."
  value       = "${aws_api_gateway_stage.prod.invoke_url}/python"
}

output "node_api_url" {
  description = "Protected Node endpoint."
  value       = "${aws_api_gateway_stage.prod.invoke_url}/node"
}

output "lambda_log_groups" {
  description = "CloudWatch log groups for the RBAC Lambda functions."

  value = {
    python = aws_cloudwatch_log_group.python_lambda.name
    node   = aws_cloudwatch_log_group.node_lambda.name
  }
}

output "waf_web_acl_arn" {
  description = "ARN of the Lab E regional WAF Web ACL."
  value       = aws_wafv2_web_acl.main.arn
}

output "waf_log_group" {
  description = "CloudWatch log group receiving WAF logs."
  value       = aws_cloudwatch_log_group.waf.name
}
