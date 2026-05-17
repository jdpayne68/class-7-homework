#API Gateway

resource "aws_api_gateway_rest_api" "rest_api_gateway" {
  name = "${local.name_prefix}-rest-api-gateway"
}

resource "aws_api_gateway_resource" "python_resource" {
  rest_api_id = aws_api_gateway_rest_api.rest_api_gateway.id
  parent_id   = aws_api_gateway_rest_api.rest_api_gateway.root_resource_id
  path_part   = "python"

}

resource "aws_api_gateway_resource" "node_resource" {
  rest_api_id = aws_api_gateway_rest_api.rest_api_gateway.id
  parent_id   = aws_api_gateway_rest_api.rest_api_gateway.root_resource_id
  path_part   = "node"

}

resource "aws_api_gateway_method" "python_method" {
  resource_id   = aws_api_gateway_resource.python_resource.id
  rest_api_id   = aws_api_gateway_rest_api.rest_api_gateway.id
  authorization = "NONE"
  http_method   = "GET"
}

resource "aws_api_gateway_method" "node_method" {
  resource_id   = aws_api_gateway_resource.node_resource.id
  rest_api_id   = aws_api_gateway_rest_api.rest_api_gateway.id
  authorization = "NONE"
  http_method   = "GET"
}

resource "aws_api_gateway_integration" "python_integration" {
  resource_id = aws_api_gateway_resource.python_resource.id
  rest_api_id = aws_api_gateway_rest_api.rest_api_gateway.id
  http_method = aws_api_gateway_method.python_method.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.python.invoke_arn
}

resource "aws_api_gateway_integration" "node_integration" {
  resource_id = aws_api_gateway_resource.node_resource.id
  rest_api_id = aws_api_gateway_rest_api.rest_api_gateway.id
  http_method = aws_api_gateway_method.node_method.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.node.invoke_arn
}


resource "aws_api_gateway_deployment" "rest_api_deployment" {
  rest_api_id = aws_api_gateway_rest_api.rest_api_gateway.id

  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.python_resource.id,
      aws_api_gateway_resource.node_resource.id,
      aws_api_gateway_method.python_method.http_method,
      aws_api_gateway_method.node_method.http_method,
      aws_api_gateway_integration.python_integration.uri,
      aws_api_gateway_integration.node_integration.uri,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "prod_stage" {
  stage_name    = "prod"
  rest_api_id   = aws_api_gateway_rest_api.rest_api_gateway.id
  deployment_id = aws_api_gateway_deployment.rest_api_deployment.id
}



















