# Architecture

## Purpose

Switchyard is a narrow control plane for approved network changes: DNS,
load balancer routes, TLS bindings, and security group rules. It is not a
general cloud management platform.

## Request pipeline

1. API accepts a typed request (no raw HCL).
2. Domain layer validates and produces a **normalized change specification**.
3. Infrastructure layer renders Terraform module inputs/composition from that
   specification.
4. `terraform plan` produces a saved plan binary, plan JSON, and artifact hash
   (required path: local terraform and/or fixtures).
5. OPA/Conftest evaluates plan JSON (plus inventory fixtures).
6. Request enters `awaiting_approval` workflow state.
7. Approval boundary: required DoD uses a simulated gate; optional real deploy
   uses GitHub Environment protection.
8. Apply verifies the plan artifact hash, then applies that exact plan
   (required: local/mock backend; optional: AWS).
9. DNS/TCP verification runs (required: local doubles; optional: real endpoints).
10. Audit and metrics are recorded.

## Environment isolation

Separate Terraform state roots for `dev`, `staging`, and `prod` (no
workspaces). See [ADR-0001](adr/0001-environment-state-isolation.md).

No environment must be provisioned in AWS for Definition of Done.

## Zero cost

Definition of Done is $0. See [cost.md](cost.md) and
[ADR-0003](adr/0003-local-vs-aws-execution.md).

## Key documents

- [ADR-0002 — Saved plan apply binding](adr/0002-saved-plan-apply-binding.md)
- [ADR-0003 — Local vs optional AWS](adr/0003-local-vs-aws-execution.md)
