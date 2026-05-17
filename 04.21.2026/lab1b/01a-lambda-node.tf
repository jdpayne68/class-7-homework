resource "aws_lambda_function" "node" {
  function_name = "${local.name_prefix}-node-lambda"
  role          = aws_iam_role.lambda_role.arn
  handler       = "index.handler"
  runtime       = "nodejs24.x"

  filename         = data.archive_file.node_zip.output_path
  source_code_hash = data.archive_file.node_zip.output_base64sha256
}

# zip node.zip index.js
data "archive_file" "node_zip" {
  type        = "zip"
  output_path = "${path.module}/node-lambda.zip"

  source {
    content  = file("${path.module}/${local.name_prefix}-node-lambda.js")
    filename = "index.js"
  }
}

####################################
#Terraform Registry Documentation
####################################
#archive_file(Resource): https://registry.terraform.io/providers/hashicorp/archive/latest/docs/data-sources/file

#Used to generate an archive file (zip) from a source file (index.js and lambda_function.py) for Lambda deployment.