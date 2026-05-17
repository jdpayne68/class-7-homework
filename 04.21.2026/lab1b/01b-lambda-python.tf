resource "aws_lambda_function" "python" {
  function_name = "${local.name_prefix}-python-lambda"
  role          = aws_iam_role.lambda_role.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.12"

  filename         = data.archive_file.python_zip.output_path
  source_code_hash = data.archive_file.python_zip.output_base64sha256
}

# zip python.zip lambda_function.py
data "archive_file" "python_zip" {
  type        = "zip"
  output_path = "${path.module}/python-lambda.zip"

  source {
    content  = file("${path.module}/${local.name_prefix}-python-lambda.py")
    filename = "lambda_function.py"
  }
}


####################################
#Terraform Registry Documentation
####################################
#archive_file(Resource): https://registry.terraform.io/providers/hashicorp/archive/latest/docs/data-sources/file

#Used to generate an archive file (zip) from a source file (index.js and lambda_function.py) for Lambda deployment.