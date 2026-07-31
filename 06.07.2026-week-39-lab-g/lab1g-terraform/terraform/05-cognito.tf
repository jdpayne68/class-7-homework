resource "aws_cognito_user_pool" "lab" {
  name              = "${var.project_name}-user-pool"
  mfa_configuration = "OFF"

  admin_create_user_config {
    allow_admin_create_user_only = true
  }

  password_policy {
    minimum_length                   = 12
    require_lowercase                = true
    require_numbers                  = true
    require_symbols                  = true
    require_uppercase                = true
    temporary_password_validity_days = 1
  }

  username_configuration {
    case_sensitive = false
  }
}

resource "aws_cognito_user_pool_client" "lab" {
  name         = "${var.project_name}-client"
  user_pool_id = aws_cognito_user_pool.lab.id

  generate_secret = false

  explicit_auth_flows = [
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_USER_PASSWORD_AUTH",
  ]

  access_token_validity  = 1
  id_token_validity      = 1
  refresh_token_validity = 1

  token_validity_units {
    access_token  = "hours"
    id_token      = "hours"
    refresh_token = "days"
  }

  enable_token_revocation       = true
  prevent_user_existence_errors = "ENABLED"
}
