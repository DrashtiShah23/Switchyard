output "rule_arn" {
  description = "ARN of the listener rule."
  value       = aws_lb_listener_rule.this.arn
}

output "rule_id" {
  description = "ID of the listener rule."
  value       = aws_lb_listener_rule.this.id
}

output "priority" {
  description = "Priority of the listener rule."
  value       = aws_lb_listener_rule.this.priority
}

output "listener_arn" {
  description = "Listener ARN the rule is attached to."
  value       = aws_lb_listener_rule.this.listener_arn
}
