provider "aws" {
  region                      = "us-west-2"
  access_key                  = "mock"
  secret_key                  = "mock"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
}

variables {
  zone_id         = "Z3P5QSUBK4LQIN"
  record_name     = "app.example.com"
  record_type     = "A"
  ttl_seconds     = 300
  records         = ["1.2.3.4"]
  allow_overwrite = true
  tags            = {}
}

run "rejects_invalid_zone_id" {
  command = plan

  variables {
    zone_id = "not-a-zone"
  }

  expect_failures = [
    var.zone_id,
  ]
}

run "rejects_unsupported_record_type" {
  command = plan

  variables {
    record_type = "MX"
  }

  expect_failures = [
    var.record_type,
  ]
}

run "rejects_low_ttl" {
  command = plan

  variables {
    ttl_seconds = 30
  }

  expect_failures = [
    var.ttl_seconds,
  ]
}

run "rejects_cname_with_multiple_values" {
  command = plan

  variables {
    record_type = "CNAME"
    records     = ["a.example.com", "b.example.com"]
  }

  expect_failures = [
    check.cname_single_value,
  ]
}
