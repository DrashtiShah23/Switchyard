locals {
  base_tags = merge(
    {
      Project   = "switchyard"
      Component = "dns"
      ManagedBy = "terraform"
    },
    var.tags,
  )
}

# Intentionally absent: aws_route53_zone.
# Hosted zones can incur cost and are owned by environment binding, not callers.

resource "aws_route53_record" "this" {
  zone_id         = var.zone_id
  name            = var.record_name
  type            = var.record_type
  ttl             = var.ttl_seconds
  records         = var.records
  allow_overwrite = var.allow_overwrite
}
