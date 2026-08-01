variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "project_name" {
  type    = string
  default = "jacques-lab-h-waf"
}

variable "bedrock_model_id" {
  type    = string
  default = "us.anthropic.claude-sonnet-4-6"
}

variable "lookback_minutes" {
  type    = number
  default = 10
}

variable "max_events" {
  type    = number
  default = 5
}

variable "bedrock_max_tokens" {
  type    = number
  default = 1100
}

variable "schedule_expression" {
  type    = string
  default = "rate(5 minutes)"
}
