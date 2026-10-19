# tls module

Attaches an existing ACM certificate ARN to an ALB listener
(`aws_lb_listener_certificate`).

## Ownership

- **Does:** reference/attach an existing certificate to a listener (SNI/additional).
- **Does not:** create ACM certificates, validate DNS for issuance, or create
  Route 53 hosted zones.
- **Default certificate** on a listener (`certificate_arn` on `aws_lb_listener`)
  is owned by the `alb` module. `is_default=true` records intent for audit and
  later environment composition; it does not fabricate issuance or silently
  rewrite alb-owned listener resources.
