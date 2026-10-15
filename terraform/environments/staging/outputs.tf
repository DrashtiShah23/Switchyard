output "vpc_id" {
  description = "Staging VPC id from the network module."
  value       = module.network.vpc_id
}

output "public_subnet_ids" {
  description = "Staging public subnet ids."
  value       = module.network.public_subnet_ids
}

output "private_subnet_ids" {
  description = "Staging private subnet ids."
  value       = module.network.private_subnet_ids
}

output "nat_gateway_ids" {
  description = "Always empty — network module does not create NAT Gateways."
  value       = module.network.nat_gateway_ids
}
