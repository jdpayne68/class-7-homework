variable "aws_region" {
  description = "AWS region in which Lab E resources will be deployed."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Prefix used when naming Lab E AWS resources."
  type        = string
  default     = "jacques-lab-e-rbac"
}

variable "environment" {
  description = "Environment label applied to AWS resources."
  type        = string
  default     = "lab"
}

variable "student_group_name" {
  description = "Cognito group that receives student-level access."
  type        = string
  default     = "students"
}

variable "admin_group_name" {
  description = "Cognito group that receives administrator-level access."
  type        = string
  default     = "admins"
}

variable "log_retention_days" {
  description = "Number of days that Lambda and WAF logs are retained."
  type        = number
  default     = 7
}
