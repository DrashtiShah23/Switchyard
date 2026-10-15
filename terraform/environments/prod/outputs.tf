output "vpc_id" {
  description = "Prod VPC id from the network module."
  value       = module.network.vpc_id
}

output "public_subnet_ids" {
  description = "Prod public subnet ids."
  value       = module.network.public_subnet_ids
}

output "private_subnet_ids" {
  description = "Prod private subnet ids."
  value       = module.network.private_subnet_ids
}

output "nat_gateway_ids" {
  description = "Always empty — network module does not create NAT Gateways."
  value       = module.network.nat_gateway_ids
}
