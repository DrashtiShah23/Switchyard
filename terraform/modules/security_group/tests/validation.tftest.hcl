provider "aws" {
  region                      = "us-west-2"
  access_key                  = "mock"
  secret_key                  = "mock"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
}

variables {
  create_security_group = true
  name                  = "switchyard-app"
  vpc_id                = "vpc-0123456789abcdef0"
  description           = "test"
  ingress_rules = [
    {
      description = "https"
      protocol    = "tcp"
      from_port   = 443
      to_port     = 443
      cidr_ipv4   = "10.0.0.0/8"
    },
  ]
  egress_rules = []
  tags         = {}
}

run "rejects_invalid_existing_sg_id_shape" {
  command = plan

  variables {
    create_security_group      = false
    existing_security_group_id = "not-an-sg"
    name                       = null
    vpc_id                     = null
    ingress_rules              = []
  }

  expect_failures = [
    var.existing_security_group_id,
  ]
}

run "rejects_open_ssh_ingress" {
  command = plan

  variables {
    ingress_rules = [
      {
        description = "ssh open"
        protocol    = "tcp"
        from_port   = 22
        to_port     = 22
        cidr_ipv4   = "0.0.0.0/0"
      },
    ]
  }

  expect_failures = [
    check.no_open_admin_ingress,
  ]
}

# Note: ambiguous dual-source rules are enforced by check.rules_have_exactly_one_source
# on real plans. A terraform test that feeds both attributes also trips AWS provider
# schema validation before the check block, so dual-source rejection is covered by
# domain validation + renderer invariants instead of this file.
