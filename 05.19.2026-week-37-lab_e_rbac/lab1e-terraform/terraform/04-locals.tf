locals {
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
    Lab         = "E-RBAC"
  }

  user_pool_name       = "${var.project_name}-user-pool"
  api_name             = "${var.project_name}-api"
  authorizer_name      = "${var.project_name}-cognito-authorizer"
  python_function_name = "${var.project_name}-python"
  node_function_name   = "${var.project_name}-node"
  lambda_role_name     = "${var.project_name}-lambda-role"
  waf_name             = "${var.project_name}-waf"
  waf_log_group_name   = "aws-waf-logs-${var.project_name}"
}
