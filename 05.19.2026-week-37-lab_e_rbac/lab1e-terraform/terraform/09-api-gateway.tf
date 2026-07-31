resource "aws_api_gateway_rest_api" "main" {
  name        = local.api_name
  description = "Lab E REST API protected by Cognito authentication and Lambda RBAC."

  endpoint_configuration {
    types = ["REGIONAL"]
  }
}

resource "aws_api_gateway_resource" "python" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "python"
}

resource "aws_api_gateway_resource" "node" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "node"
}

resource "aws_api_gateway_authorizer" "cognito" {
  name            = local.authorizer_name
  rest_api_id     = aws_api_gateway_rest_api.main.id
  type            = "COGNITO_USER_POOLS"
  provider_arns   = [aws_cognito_user_pool.main.arn]
  identity_source = "method.request.header.Authorization"
}

resource "aws_api_gateway_method" "python_get" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.python.id
  http_method   = "GET"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito.id
}

resource "aws_api_gateway_method" "node_get" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.node.id
  http_method   = "GET"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito.id
}

resource "aws_api_gateway_integration" "python" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.python.id
  http_method = aws_api_gateway_method.python_get.http_method

  type                    = "AWS_PROXY"
  integration_http_method = "POST"
  uri                     = aws_lambda_function.python.invoke_arn
}

resource "aws_api_gateway_integration" "node" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.node.id
  http_method = aws_api_gateway_method.node_get.http_method

  type                    = "AWS_PROXY"
  integration_http_method = "POST"
  uri                     = aws_lambda_function.node.invoke_arn
}

resource "aws_lambda_permission" "api_gateway_python" {
  statement_id  = "AllowSpecificApiGatewayPythonRoute"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.python.function_name
  principal     = "apigateway.amazonaws.com"

  source_arn = "${aws_api_gateway_rest_api.main.execution_arn}/*/GET/python"
}

resource "aws_lambda_permission" "api_gateway_node" {
  statement_id  = "AllowSpecificApiGatewayNodeRoute"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.node.function_name
  principal     = "apigateway.amazonaws.com"

  source_arn = "${aws_api_gateway_rest_api.main.execution_arn}/*/GET/node"
}

resource "aws_api_gateway_deployment" "main" {
  rest_api_id = aws_api_gateway_rest_api.main.id

  triggers = {
    redeployment = sha1(
      jsonencode(
        [
          aws_api_gateway_authorizer.cognito.id,
          aws_api_gateway_method.python_get.id,
          aws_api_gateway_method.node_get.id,
          aws_api_gateway_integration.python.id,
          aws_api_gateway_integration.node.id,
        ]
      )
    )
  }

  lifecycle {
    create_before_destroy = true
  }

  depends_on = [
    aws_api_gateway_integration.python,
    aws_api_gateway_integration.node,
  ]
}

resource "aws_api_gateway_stage" "prod" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  deployment_id = aws_api_gateway_deployment.main.id
  stage_name    = "prod"
}
