resource "aws_api_gateway_rest_api" "lab" {
  name = "${var.project_name}-api"

  endpoint_configuration {
    types = ["REGIONAL"]
  }
}

resource "aws_api_gateway_resource" "protected" {
  rest_api_id = aws_api_gateway_rest_api.lab.id
  parent_id   = aws_api_gateway_rest_api.lab.root_resource_id
  path_part   = "protected"
}

resource "aws_api_gateway_authorizer" "cognito" {
  name            = "${var.project_name}-cognito-authorizer"
  rest_api_id     = aws_api_gateway_rest_api.lab.id
  type            = "COGNITO_USER_POOLS"
  provider_arns   = [aws_cognito_user_pool.lab.arn]
  identity_source = "method.request.header.Authorization"
}

resource "aws_api_gateway_method" "protected_get" {
  rest_api_id   = aws_api_gateway_rest_api.lab.id
  resource_id   = aws_api_gateway_resource.protected.id
  http_method   = "GET"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito.id
}

resource "aws_api_gateway_integration" "protected_get" {
  rest_api_id             = aws_api_gateway_rest_api.lab.id
  resource_id             = aws_api_gateway_resource.protected.id
  http_method             = aws_api_gateway_method.protected_get.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.protected_api.invoke_arn
}

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowApiGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.protected_api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.lab.execution_arn}/*/*"
}

resource "aws_api_gateway_deployment" "lab" {
  rest_api_id = aws_api_gateway_rest_api.lab.id

  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.protected.id,
      aws_api_gateway_method.protected_get.id,
      aws_api_gateway_integration.protected_get.id,
      aws_api_gateway_authorizer.cognito.id,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }

  depends_on = [
    aws_api_gateway_integration.protected_get,
    aws_lambda_permission.api_gateway,
  ]
}

resource "aws_api_gateway_stage" "prod" {
  deployment_id = aws_api_gateway_deployment.lab.id
  rest_api_id   = aws_api_gateway_rest_api.lab.id
  stage_name    = "prod"
}
