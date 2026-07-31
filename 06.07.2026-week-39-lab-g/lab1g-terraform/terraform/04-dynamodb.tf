resource "aws_dynamodb_table" "token_tracking" {
  name         = "token-tracking"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "token_id"

  attribute {
    name = "token_id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = false
  }
}
