# security_group module

Creates a VPC security group and/or manages discrete ingress/egress rules.

## Modes

- `create_security_group = true` — requires `vpc_id` + `name` (typically the
  network module `vpc_id` output).
- `create_security_group = false` — requires `existing_security_group_id` and only
  manages rule resources (matches Switchyard SG *rule* change requests).

## Safety

- Rejects open administrative ingress to `0.0.0.0/0` on ports 22/3389 via a
  Terraform `check` block.
- Does not query live AWS inventory for CIDR overlap; that remains a deferred
  authoritative check.

## Zero cost

Static `fmt` / `validate` / `terraform test` only on the required path. No NAT,
no ALB, no Route 53 hosted zone resources.
