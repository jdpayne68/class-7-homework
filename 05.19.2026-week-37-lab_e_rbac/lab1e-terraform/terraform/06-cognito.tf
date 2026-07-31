resource "aws_cognito_user_pool" "main" {
  name = local.user_pool_name

  mfa_configuration = "ON"

  software_token_mfa_configuration {
    enabled = true
  }

  admin_create_user_config {
    allow_admin_create_user_only = true
  }

  username_configuration {
    case_sensitive = false
  }

  password_policy {
    minimum_length                   = 12
    require_lowercase                = true
    require_numbers                  = true
    require_symbols                  = true
    require_uppercase                = true
    temporary_password_validity_days = 1
  }
}

resource "aws_cognito_user_group" "students" {
  name         = var.student_group_name
  user_pool_id = aws_cognito_user_pool.main.id
  description  = "Student users permitted to access the Python endpoint."
  precedence   = 20
}

resource "aws_cognito_user_group" "admins" {
  name         = var.admin_group_name
  user_pool_id = aws_cognito_user_pool.main.id
  description  = "Administrative users permitted to access Python and Node endpoints."
  precedence   = 10
}

resource "aws_cognito_user_pool_client" "main" {
  name         = "${var.project_name}-client"
  user_pool_id = aws_cognito_user_pool.main.id

  generate_secret = false

  explicit_auth_flows = [
    "ALLOW_USER_PASSWORD_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
  ]

  auth_session_validity         = 15
  access_token_validity         = 1
  id_token_validity             = 1
  refresh_token_validity        = 1
  enable_token_revocation       = true
  prevent_user_existence_errors = "ENABLED"

  token_validity_units {
    access_token  = "hours"
    id_token      = "hours"
    refresh_token = "days"
  }
}
