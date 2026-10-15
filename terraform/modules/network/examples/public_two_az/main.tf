module "network" {
  source = "../.."

  name           = var.name
  vpc_cidr       = var.vpc_cidr
  public_subnets = var.public_subnets
  # private_subnets intentionally omitted — no NAT path in this example.
  tags = var.tags
}
