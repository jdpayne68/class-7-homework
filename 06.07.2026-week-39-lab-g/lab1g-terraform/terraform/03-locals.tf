locals {
  common_tags = {
    Project   = var.project_name
    Lab       = "G"
    ManagedBy = "Terraform"
  }

  protected_lambda_name = "${var.project_name}-protected-api"
  detector_lambda_name  = "${var.project_name}-detector"

  bedrock_foundation_model_id = trimprefix(var.bedrock_model_id, "us.")

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
