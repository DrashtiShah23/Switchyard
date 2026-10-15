output "vpc_id" {
  description = "ID of the VPC."
  value       = aws_vpc.this.id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC."
  value       = aws_vpc.this.cidr_block
}

output "internet_gateway_id" {
  description = "ID of the Internet Gateway attached to the VPC."
  value       = aws_internet_gateway.this.id
}

output "public_subnet_ids" {
  description = "Public subnet IDs in declaration order."
  value       = [for key in sort(keys(aws_subnet.public)) : aws_subnet.public[key].id]
}

output "public_subnet_cidrs" {
  description = "Public subnet CIDR blocks in declaration order."
  value       = [for key in sort(keys(aws_subnet.public)) : aws_subnet.public[key].cidr_block]
}

output "public_subnet_availability_zones" {
  description = "Availability zones for public subnets in declaration order."
  value       = [for key in sort(keys(aws_subnet.public)) : aws_subnet.public[key].availability_zone]
}

output "private_subnet_ids" {
  description = "Private subnet IDs in declaration order (empty when unused)."
  value       = [for key in sort(keys(aws_subnet.private)) : aws_subnet.private[key].id]
}

output "public_route_table_id" {
  description = "Route table ID used by public subnets."
  value       = aws_route_table.public.id
}

output "private_route_table_id" {
  description = "Route table ID used by private subnets, if any."
  value       = try(aws_route_table.private[0].id, null)
}

output "nat_gateway_ids" {
  description = "Always empty — this module never creates NAT Gateways."
  value       = []
}
