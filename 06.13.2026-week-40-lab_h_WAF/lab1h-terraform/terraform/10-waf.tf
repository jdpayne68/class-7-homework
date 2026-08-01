resource "aws_wafv2_web_acl" "api" {
  name  = "${var.project_name}-web-acl"
  scope = "REGIONAL"

  default_action {
    allow {}
  }

  rule {
    name     = "AWSManagedCommonRules"
    priority = 1

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        vendor_name = "AWS"
        name        = "AWSManagedRulesCommonRuleSet"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${var.project_name}-common-rules"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${var.project_name}-web-acl"
    sampled_requests_enabled   = true
  }
}

resource "aws_wafv2_web_acl_association" "api_stage" {
  resource_arn = join(
    "",
    [
      "arn:",
      data.aws_partition.current.partition,
      ":apigateway:",
      var.aws_region,
      "::/restapis/",
      aws_api_gateway_rest_api.waf_api.id,
      "/stages/",
      aws_api_gateway_stage.prod.stage_name,
    ]
  )

  web_acl_arn = aws_wafv2_web_acl.api.arn
}

resource "aws_wafv2_web_acl_logging_configuration" "api" {
  resource_arn = aws_wafv2_web_acl.api.arn

  log_destination_configs = [
    aws_cloudwatch_log_group.waf.arn,
  ]
}
