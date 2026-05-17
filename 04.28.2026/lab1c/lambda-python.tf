resource "aws_lambda_function" "python" {
  function_name = "chewbacca-python-lambda"
  role          = aws_iam_role.lambda_role.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.11"

  filename = "python.zip"
}

# zip python.zip lambda_function.py

