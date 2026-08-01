locals {
  common_tags = {
    Project   = var.project_name
    Lab       = "H"
    ManagedBy = "Terraform"
  }

  api_lambda_name      = "${var.project_name}-api"
  analyzer_lambda_name = "${var.project_name}-analyzer"
  waf_log_group_name   = "aws-waf-logs-${var.project_name}"

  bedrock_foundation_model_id = trimprefix(
    var.bedrock_model_id,
    "us.",
  )

  bedrock_inference_profile_arn = join(
    ":",
    [
      "arn",
      data.aws_partition.current.partition,
      "bedrock",
      var.aws_region,
      data.aws_caller_identity.current.account_id,
      "inference-profile/${var.bedrock_model_id}",
    ]
  )

  bedrock_foundation_model_arn = join(
    ":",
    [
      "arn",
      data.aws_partition.current.partition,
      "bedrock",
      "*",
      "",
      "foundation-model/${local.bedrock_foundation_model_id}",
    ]
  )
}
