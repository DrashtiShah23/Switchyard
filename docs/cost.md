# Cost discipline

Switchyard’s AWS path validates the **control plane**, not a highly available
production network.

## Locked constraints

| Constraint | Rationale |
|---|---|
| Single AZ | Enough to exercise modules and workflows |
| No NAT Gateway | Avoid unnecessary recurring cost |
| Short-lived resources | Destroy the same day after validation |
| Provision `dev` only | Staging/prod keep config + isolated state design without paid infra |
| ALB fixed-response preferred | Proves listener/route automation without EC2 targets |

Do not expand the demo into multi-AZ “production Box” networking.

## Potentially billable resources

| Resource | Risk | Notes |
|---|---|---|
| Application Load Balancer | Primary | Create only during E2E; destroy immediately after |
| Route 53 hosted zone | Low | Short-lived or reuse an existing zone briefly |
| S3 state bucket | Very low | Empty storage is cheap; optional retain |
| VPC / SG / ACM (public) | Negligible / free | No NAT |

## Operator checklist

1. Tag every resource with project and owner metadata.
2. Run validation only as long as needed.
3. Run `make destroy-sandbox` (Milestone 16) before ending the day.
4. Never leave an ALB running “for later.”
