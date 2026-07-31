variable "aws_region" {
  description = "AWS region for Lab G."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Resource-name prefix."
  type        = string
  default     = "jacques-lab-g-ai-soar"
}

variable "alert_after_minutes" {
  description = "Age threshold for unused-token alerts."
  type        = number
  default     = 10
}

variable "bedrock_model_id" {
  description = "Amazon Bedrock inference profile used for SOC enrichment."
  type        = string
  default     = "us.anthropic.claude-sonnet-4-6"
}

variable "bedrock_max_tokens" {
  description = "Maximum output tokens for each AI enrichment."
  type        = number
  default     = 1400
}
