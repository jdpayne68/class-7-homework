resource "aws_lambda_function" "node" {
  function_name = "chewbacca-node-lambda"
  role          = aws_iam_role.lambda_role.arn
  handler       = "index.handler"
  runtime       = "nodejs18.x"

  filename = "node.zip"
}

# zip node.zip index.js
