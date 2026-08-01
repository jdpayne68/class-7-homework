resource "aws_scheduler_schedule" "analyzer" {
  name                = "${var.project_name}-analyzer"
  schedule_expression = var.schedule_expression
  state               = "ENABLED"

  flexible_time_window {
    mode = "OFF"
  }

  target {
    arn      = aws_lambda_function.analyzer.arn
    role_arn = aws_iam_role.scheduler.arn

    input = jsonencode(
      {
        source = "eventbridge-scheduler"
      }
    )
  }
}
