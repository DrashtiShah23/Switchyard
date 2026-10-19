provider "aws" {
  region                      = "us-west-2"
  access_key                  = "mock"
  secret_key                  = "mock"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
}

variables {
  name               = "switchyard-app"
  subnet_ids         = ["subnet-aaa111", "subnet-bbb222"]
  security_group_ids = ["sg-0123456789abcdef0"]
  listeners = [
    {
      port     = 80
      protocol = "HTTP"
      default_action = {
        type        = "fixed-response"
        status_code = "200"
      }
    },
  ]
  tags = {}
}

run "rejects_single_subnet" {
  command = plan

  variables {
    subnet_ids = ["subnet-only-one"]
  }

  expect_failures = [
    var.subnet_ids,
  ]
}

run "rejects_https_without_certificate" {
  command = plan

  variables {
    listeners = [
      {
        port     = 443
        protocol = "HTTPS"
        default_action = {
          type        = "fixed-response"
          status_code = "200"
        }
      },
    ]
  }

  expect_failures = [
    check.https_requires_certificate,
  ]
}

run "rejects_http_on_443" {
  command = plan

  variables {
    listeners = [
      {
        port     = 443
        protocol = "HTTP"
        default_action = {
          type        = "fixed-response"
          status_code = "200"
        }
      },
    ]
  }

  expect_failures = [
    check.http_should_not_use_443,
  ]
}
