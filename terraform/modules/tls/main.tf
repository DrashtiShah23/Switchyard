locals {
  base_tags = merge(
    {
      Project   = "switchyard"
      Component = "tls"
      ManagedBy = "terraform"
      # Audit intent for default vs additional attachment.
      DefaultCertificateIntent = var.is_default ? "true" : "false"
    },
    var.tags,
  )
}

# Certificate reference/attachment only. Never creates aws_acm_certificate.
resource "aws_lb_listener_certificate" "this" {
  listener_arn    = var.listener_arn
  certificate_arn = var.certificate_arn
}
