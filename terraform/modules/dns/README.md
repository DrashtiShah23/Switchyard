# dns module

Manages a single Route 53 record inside an **existing** hosted zone.

## Guarantees

- Never creates `aws_route53_zone` (avoids billable zone creation on the
  required path).
- `zone_id` comes from environment binding / render context — not from arbitrary
  caller HCL.
- Duplicate ownership against live Route 53 is **not** checked here; that is a
  deferred authoritative inventory concern.

## Example

See `examples/record/`.
