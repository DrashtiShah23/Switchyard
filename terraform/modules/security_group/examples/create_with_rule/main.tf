module "security_group" {
  source = "../.."

  create_security_group = true
  name                  = "switchyard-app"
  vpc_id                = "vpc-0123456789abcdef0"
  description           = "Example app security group"

  ingress_rules = [
    {
      description = "https from corp"
      protocol    = "tcp"
      from_port   = 443
      to_port     = 443
      cidr_ipv4   = "10.0.0.0/8"
    },
  ]

  egress_rules = [
    {
      description = "allow all egress"
      protocol    = "-1"
      cidr_ipv4   = "0.0.0.0/0"
    },
  ]

  tags = {
    Owner = "switchyard-local"
  }
}
