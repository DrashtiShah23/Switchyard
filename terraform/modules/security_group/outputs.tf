output "security_group_id" {
  description = "ID of the managed or referenced security group."
  value       = local.security_group_id
}

output "security_group_arn" {
  description = "ARN of a created security group, if create_security_group is true."
  value       = try(aws_security_group.this[0].arn, null)
}

output "ingress_rule_ids" {
  description = "IDs of managed ingress rules."
  value       = [for key in sort(keys(aws_vpc_security_group_ingress_rule.this)) : aws_vpc_security_group_ingress_rule.this[key].id]
}

output "egress_rule_ids" {
  description = "IDs of managed egress rules."
  value       = [for key in sort(keys(aws_vpc_security_group_egress_rule.this)) : aws_vpc_security_group_egress_rule.this[key].id]
}
