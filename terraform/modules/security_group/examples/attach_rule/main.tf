module "security_group" {
  source = "../.."

  create_security_group      = false
  existing_security_group_id = "sg-0123456789abcdef0"

  ingress_rules = [
    {
      description = "app traffic"
      protocol    = "tcp"
      from_port   = 8080
      to_port     = 8080
      cidr_ipv4   = "10.10.0.0/16"
    },
  ]
}
