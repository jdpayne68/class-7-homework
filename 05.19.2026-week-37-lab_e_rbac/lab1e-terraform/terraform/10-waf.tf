resource "aws_cloudwatch_log_group" "waf" {
  name              = local.waf_log_group_name
  retention_in_days = var.log_retention_days
}

resource "aws_wafv2_web_acl" "main" {
  name        = local.waf_name
  description = "Regional WAF protecting the Lab E API Gateway stage."
  scope       = "REGIONAL"

  default_action {
    allow {}
  }

  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 10

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${var.project_name}-common-rules"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "RateLimitPerClientIP"
    priority = 20

    action {
      block {}
    }

    statement {
      rate_based_statement {
        aggregate_key_type = "IP"
        limit              = 1000
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${var.project_name}-rate-limit"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = local.waf_name
    sampled_requests_enabled   = true
  }
}

resource "aws_wafv2_web_acl_association" "api_gateway" {
  resource_arn = "arn:${data.aws_partition.current.partition}:apigateway:${data.aws_region.current.region}::/restapis/${aws_api_gateway_rest_api.main.id}/stages/${aws_api_gateway_stage.prod.stage_name}"
  web_acl_arn  = aws_wafv2_web_acl.main.arn
}

resource "aws_wafv2_web_acl_logging_configuration" "main" {
  resource_arn            = aws_wafv2_web_acl.main.arn
  log_destination_configs = [aws_cloudwatch_log_group.waf.arn]

  redacted_fields {
    single_header {
      name = "authorization"
    }
  }

  depends_on = [
    aws_wafv2_web_acl_association.api_gateway,
  ]
}
