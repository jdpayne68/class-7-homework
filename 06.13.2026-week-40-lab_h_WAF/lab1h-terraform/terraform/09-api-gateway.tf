resource "aws_api_gateway_rest_api" "waf_api" {
  name        = "${var.project_name}-api"
  description = "REST API protected by AWS WAF"

  endpoint_configuration {
    types = ["REGIONAL"]
  }
}

resource "aws_api_gateway_resource" "analyze" {
  rest_api_id = aws_api_gateway_rest_api.waf_api.id
  parent_id   = aws_api_gateway_rest_api.waf_api.root_resource_id
  path_part   = "analyze"
}

resource "aws_api_gateway_method" "get_analyze" {
  rest_api_id   = aws_api_gateway_rest_api.waf_api.id
  resource_id   = aws_api_gateway_resource.analyze.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "api_lambda" {
  rest_api_id = aws_api_gateway_rest_api.waf_api.id
  resource_id = aws_api_gateway_resource.analyze.id
  http_method = aws_api_gateway_method.get_analyze.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.api.invoke_arn
}

resource "aws_api_gateway_deployment" "prod" {
  rest_api_id = aws_api_gateway_rest_api.waf_api.id

  triggers = {
    redeployment = sha1(
      jsonencode(
        [
          aws_api_gateway_resource.analyze.id,
          aws_api_gateway_method.get_analyze.id,
          aws_api_gateway_integration.api_lambda.id,
        ]
      )
    )
  }

  lifecycle {
    create_before_destroy = true
  }

  depends_on = [aws_api_gateway_integration.api_lambda]
}

resource "aws_api_gateway_stage" "prod" {
  deployment_id = aws_api_gateway_deployment.prod.id
  rest_api_id   = aws_api_gateway_rest_api.waf_api.id
  stage_name    = "prod"
}

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowExecutionFromApiGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.waf_api.execution_arn}/*/GET/analyze"
}
