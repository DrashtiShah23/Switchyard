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
  priority     = 10
  path_pattern = "/health"
  host_header  = null
  action = {
    type        = "fixed-response"
    status_code = "200"
  }
  tags = {}
}

run "rejects_bad_listener_arn" {
  command = plan

  variables {
    listener_arn = "not-an-arn"
  }

  expect_failures = [
    var.listener_arn,
  ]
}

run "rejects_priority_out_of_range" {
  command = plan

  variables {
    priority = 0
  }

  expect_failures = [
    var.priority,
  ]
}

# Missing path/host conditions are enforced by check.at_least_one_condition on
# real plans and by domain/renderer validation. Feeding both nulls also trips
# the AWS provider schema ("at least 1 condition block") before the check runs.
