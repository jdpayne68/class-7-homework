variable "aws_region" {
  description = "AWS region for Lab F."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Resource-name prefix."
  type        = string
  default     = "jacques-lab-f-unused-token"
}

variable "alert_after_minutes" {
  description = "Age threshold for unused-token alerts."
  type        = number
  default     = 10
}
