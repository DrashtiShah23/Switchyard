# alb module

Creates an Application Load Balancer and its listeners.

## Inputs from other modules

- `subnet_ids` ← `network.public_subnet_ids` (≥2)
- `security_group_ids` ← `security_group.security_group_id` (explicit SG ownership)

## Outputs for later composition

- `load_balancer_dns_name` / `load_balancer_zone_id` → DNS alias records
- `listener_arns_by_port` → `listener_rule` and `tls` modules

## TLS

HTTPS listeners accept an ACM `certificate_arn` **reference** only. This module
never creates ACM certificates or Route 53 hosted zones.

## Zero cost

Required path is `fmt` / `validate` / `terraform test` only. Do not apply an
ALB unless an operator explicitly opts into optional cloud validation.
