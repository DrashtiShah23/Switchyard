# Variable-validation unit tests. These fail before provider apply and do not
# require real AWS credentials or billable resources.

provider "aws" {
  region                      = "us-west-2"
  access_key                  = "mock"
  secret_key                  = "mock"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
}

variables {
  name     = "switchyard"
  vpc_cidr = "10.10.0.0/16"
  public_subnets = [
    {
      availability_zone = "us-west-2a"
      cidr_block        = "10.10.1.0/24"
    },
  ]
  private_subnets = []
  tags            = {}
}

run "rejects_invalid_name" {
  command = plan

  variables {
    name = "INVALID_NAME"
  }

  expect_failures = [
    var.name,
  ]
}

run "rejects_invalid_vpc_cidr" {
  command = plan

  variables {
    vpc_cidr = "not-a-cidr"
  }

  expect_failures = [
    var.vpc_cidr,
  ]
}

run "rejects_empty_public_subnets" {
  command = plan

  variables {
    public_subnets = []
  }

  expect_failures = [
    var.public_subnets,
  ]
}

run "rejects_invalid_public_subnet_cidr" {
  command = plan

  variables {
    public_subnets = [
      {
        availability_zone = "us-west-2a"
        cidr_block        = "bad"
      },
    ]
  }

  expect_failures = [
    var.public_subnets,
  ]
}
