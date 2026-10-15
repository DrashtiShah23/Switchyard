# Architecture

> Stub for Milestone 1. Expand as components land.

## Purpose

Switchyard is a narrow control plane for approved network changes: DNS,
load balancer routes, TLS bindings, and security group rules. It is not a
general cloud management platform.

## Request pipeline

1. API accepts a typed request (no raw HCL).
2. Domain layer validates and produces a **normalized change specification**.
3. Infrastructure layer renders Terraform module inputs/composition from that
   specification.
4. `terraform plan` produces a saved plan binary, plan JSON, and artifact hash.
5. OPA/Conftest evaluates plan JSON (plus inventory fixtures in local tests).
6. Request enters `awaiting_approval` workflow state.
7. **GitHub Environment approval** is authoritative for real infrastructure
   deployment.
8. Apply verifies the plan artifact hash, then applies that exact plan.
9. DNS/TCP verification runs; audit and metrics are recorded.

## Environment isolation

Separate Terraform state roots for `dev`, `staging`, and `prod` (no
workspaces). See [ADR-0001](adr/0001-environment-state-isolation.md).

Only **dev** is provisioned for the portfolio demonstration.

## Key documents

- [ADR-0002 — Saved plan apply binding](adr/0002-saved-plan-apply-binding.md)
- [ADR-0003 — Local vs AWS execution](adr/0003-local-vs-aws-execution.md)
- [Cost discipline](cost.md)
