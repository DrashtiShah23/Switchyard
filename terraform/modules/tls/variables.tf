variable "listener_arn" {
  type        = string
  description = "ARN of an existing HTTPS/TLS listener."

  validation {
    condition     = can(regex("^arn:aws:elasticloadbalancing:[a-z0-9-]+:\\d{12}:listener/.+$", var.listener_arn))
    error_message = "listener_arn must be a valid ELB listener ARN."
  }
}

variable "certificate_arn" {
  type        = string
  description = "ACM certificate ARN to reference/attach. This module never issues certificates."

  validation {
    condition = can(regex(
      "^arn:aws:acm:[a-z0-9-]+:\\d{12}:certificate/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
      var.certificate_arn
    ))
    error_message = "certificate_arn must be a valid ACM certificate ARN."
  }
}

variable "is_default" {
  type        = bool
  description = <<-EOT
    When true, expresses intent that this certificate is the listener default.
    Change-request attachments always use aws_lb_listener_certificate (SNI /
    additional). Promoting a certificate to the listener default certificate_arn
    is owned by the alb module's HTTPS listener configuration in environment
    composition — never by fabricating ACM issuance here.
  EOT
  default     = false
}

variable "tags" {
  type        = map(string)
  description = "Additional tags."
  default     = {}
}
