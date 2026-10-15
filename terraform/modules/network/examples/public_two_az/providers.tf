# Static validation only — no real AWS credentials required for `validate`.
# Optional live `plan`/`apply` is operator-owned and never required for DoD.
provider "aws" {
  region                      = var.aws_region
  access_key                  = "mock"
  secret_key                  = "mock"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
}
