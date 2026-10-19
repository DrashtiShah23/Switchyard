output "listener_arn" {
  description = "Listener the certificate is attached to."
  value       = aws_lb_listener_certificate.this.listener_arn
}

output "certificate_arn" {
  description = "Attached ACM certificate ARN (reference)."
  value       = aws_lb_listener_certificate.this.certificate_arn
}

output "is_default_intent" {
  description = "Whether the change requested default-certificate intent."
  value       = var.is_default
}
