output "load_balancer_arn" {
  description = "ARN of the Application Load Balancer."
  value       = aws_lb.this.arn
}

output "load_balancer_dns_name" {
  description = "DNS name of the ALB for later Route 53 alias records."
  value       = aws_lb.this.dns_name
}

output "load_balancer_zone_id" {
  description = "Canonical hosted zone id of the ALB for Route 53 aliases."
  value       = aws_lb.this.zone_id
}

output "security_group_ids" {
  description = "Security groups attached to the ALB."
  value       = aws_lb.this.security_groups
}

output "listener_arns" {
  description = "Map of listener key to listener ARN."
  value       = { for key, listener in aws_lb_listener.this : key => listener.arn }
}

output "listener_arns_by_port" {
  description = "Map of listener port to listener ARN for route/TLS composition."
  value       = { for key, listener in aws_lb_listener.this : tostring(listener.port) => listener.arn }
}
