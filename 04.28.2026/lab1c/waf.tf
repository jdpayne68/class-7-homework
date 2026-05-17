resource "aws_wafv2_web_acl" "waf" {
  name        = "chewbacca-waf"
  scope       = "REGIONAL"
  default_action {
    allow {}
  }

  rule {
    name     = "AWSCommonRules"
    priority = 1

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
      metric_name                = "commonRules"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "waf"
    sampled_requests_enabled   = true
  }
}

# Attach WAF to API Gateway

resource "aws_wafv2_web_acl_association" "api_assoc" {
  resource_arn = aws_apigatewayv2_stage.prod.arn
  web_acl_arn  = aws_wafv2_web_acl.waf.arn
}

