data "aws_iam_policy_document" "lambda_trust" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "protected_api" {
  name               = "${var.project_name}-protected-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_trust.json
}

resource "aws_iam_role_policy_attachment" "protected_basic" {
  role       = aws_iam_role.protected_api.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

data "aws_iam_policy_document" "protected_dynamodb" {
  statement {
    actions = [
      "dynamodb:GetItem",
      "dynamodb:UpdateItem",
    ]

    resources = [aws_dynamodb_table.token_tracking.arn]
  }
}

resource "aws_iam_role_policy" "protected_dynamodb" {
  name   = "${var.project_name}-protected-dynamodb"
  role   = aws_iam_role.protected_api.id
  policy = data.aws_iam_policy_document.protected_dynamodb.json
}

resource "aws_iam_role" "detector" {
  name               = "${var.project_name}-detector-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_trust.json
}

resource "aws_iam_role_policy_attachment" "detector_basic" {
  role       = aws_iam_role.detector.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

data "aws_iam_policy_document" "detector_dynamodb" {
  statement {
    actions   = ["dynamodb:Scan"]
    resources = [aws_dynamodb_table.token_tracking.arn]
  }
}

resource "aws_iam_role_policy" "detector_dynamodb" {
  name   = "${var.project_name}-detector-dynamodb"
  role   = aws_iam_role.detector.id
  policy = data.aws_iam_policy_document.detector_dynamodb.json
}

data "aws_iam_policy_document" "detector_bedrock" {
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

resource "aws_iam_role_policy" "detector_bedrock" {
  name   = "${var.project_name}-detector-bedrock"
  role   = aws_iam_role.detector.id
  policy = data.aws_iam_policy_document.detector_bedrock.json
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
    resources = [aws_lambda_function.detector.arn]
  }
}

resource "aws_iam_role_policy" "scheduler_invoke" {
  name   = "${var.project_name}-scheduler-invoke"
  role   = aws_iam_role.scheduler.id
  policy = data.aws_iam_policy_document.scheduler_invoke.json
}
