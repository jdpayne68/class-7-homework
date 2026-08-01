locals {
  common_tags = {
    Project   = var.project_name
    Lab       = "F"
    ManagedBy = "Terraform"
  }

  protected_lambda_name = "${var.project_name}-protected-api"
  detector_lambda_name  = "${var.project_name}-detector"
}
