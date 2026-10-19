provider "aws" {
  region                      = "us-west-2"
  access_key                  = "mock"
  secret_key                  = "mock"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
}

variables {
  listener_arn = "arn:aws:elasticloadbalancing:us-west-2:123456789012:listener/app/my-alb/50dc6c495c0c9188/f2f7dc8efc522ab2"
  certificate_arn = (
    "arn:aws:acm:us-west-2:123456789012:certificate/12345678-1234-1234-1234-123456789012"
  )
  is_default = false
  tags       = {}
}

run "rejects_invalid_certificate_arn" {
  command = plan

  variables {
    certificate_arn = "arn:aws:acm:us-west-2:123456789012:certificate/not-a-uuid"
  }

  expect_failures = [
    var.certificate_arn,
  ]
}

run "rejects_invalid_listener_arn" {
  command = plan

  variables {
    listener_arn = "arn:aws:acm:us-west-2:123456789012:certificate/12345678-1234-1234-1234-123456789012"
  }

  expect_failures = [
    var.listener_arn,
  ]
}
