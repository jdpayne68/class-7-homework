data "aws_iam_policy_document" "lambda_trust" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "api" {
  name               = "${var.project_name}-api-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_trust.json
}

resource "aws_iam_role_policy_attachment" "api_basic" {
  role       = aws_iam_role.api.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role" "analyzer" {
  name               = "${var.project_name}-analyzer-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_trust.json
}

resource "aws_iam_role_policy_attachment" "analyzer_basic" {
  role       = aws_iam_role.analyzer.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

data "aws_iam_policy_document" "analyzer_logs" {
  statement {
    actions = ["logs:FilterLogEvents"]
    resources = [
      "${aws_cloudwatch_log_group.waf.arn}:*",
    ]
  }
}

resource "aws_iam_role_policy" "analyzer_logs" {
  name   = "${var.project_name}-analyzer-logs"
  role   = aws_iam_role.analyzer.id
  policy = data.aws_iam_policy_document.analyzer_logs.json
}

data "aws_iam_policy_document" "analyzer_dynamodb" {
  statement {
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
    ]
    resources = [aws_dynamodb_table.waf_events.arn]
  }
}

resource "aws_iam_role_policy" "analyzer_dynamodb" {
  name   = "${var.project_name}-analyzer-dynamodb"
  role   = aws_iam_role.analyzer.id
  policy = data.aws_iam_policy_document.analyzer_dynamodb.json
}

data "aws_iam_policy_document" "analyzer_bedrock" {
  statement {
    sid       = "InvokeConfiguredInferenceProfile"
    actions   = ["bedrock:InvokeModel"]
    resources = [local.bedrock_inference_profile_arn]
  }

  statement {
    sid       = "InvokeProfileFoundationModels"
    actions   = ["bedrock:InvokeModel"]
    resources = [local.bedrock_foundation_model_arn]

    condition {
      test     = "StringEquals"
      variable = "bedrock:InferenceProfileArn"
      values   = [local.bedrock_inference_profile_arn]
    }
  }
}

resource "aws_iam_role_policy" "analyzer_bedrock" {
  name   = "${var.project_name}-analyzer-bedrock"
  role   = aws_iam_role.analyzer.id
  policy = data.aws_iam_policy_document.analyzer_bedrock.json
}

data "aws_iam_policy_document" "scheduler_trust" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["scheduler.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "scheduler" {
  name               = "${var.project_name}-scheduler-role"
  assume_role_policy = data.aws_iam_policy_document.scheduler_trust.json
}

data "aws_iam_policy_document" "scheduler_invoke" {
  statement {
    actions   = ["lambda:InvokeFunction"]
    resources = [aws_lambda_function.analyzer.arn]
  }
}

resource "aws_iam_role_policy" "scheduler_invoke" {
  name   = "${var.project_name}-scheduler-invoke"
  role   = aws_iam_role.scheduler.id
  policy = data.aws_iam_policy_document.scheduler_invoke.json
}
