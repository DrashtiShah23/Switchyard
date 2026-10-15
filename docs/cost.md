# Cost discipline

**Hard requirement:** Switchyard’s Definition of Done is completable at **$0**.
Do not assume AWS Free Tier makes a resource free. If a cloud action can
potentially generate a charge, it is not required.

## Evidence classes

| Class | Claim language |
|---|---|
| Implemented and locally validated | Ran on a developer machine or free CI |
| Terraform defined and statically validated | `fmt` / `validate` / tflint / tests / policy fixtures |
| Optionally cloud validated | Only if a real AWS run actually happened |

Never claim AWS deployment from Terraform configuration alone.

## Required ($0) validation

- Local unit/integration/failure-injection tests
- Docker Compose for local architecture/failure behavior
- `terraform fmt`, `validate`, module/config tests
- OPA/Conftest + plan fixtures
- GitHub Actions without cloud deployment

## Forbidden in required workflows

ALB, NLB, EC2, Route 53 hosted zones, NAT Gateway, Elastic IP, ECS, RDS,
ElastiCache, or any other potentially billable cloud resource.

## Optional cloud path

Operators may run AWS validation in their own accounts. That path is **not**
part of Definition of Done. Document results only when actually executed, and
destroy promptly afterward.

## AWS-shaped without AWS bills

Terraform modules and environment roots remain in the repository so the project
stays architecturally credible for AWS. Default proof is static and local, not
a live bill.
