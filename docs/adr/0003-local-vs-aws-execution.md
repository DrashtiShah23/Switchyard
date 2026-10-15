# ADR-0003: Zero-cost local validation vs optional AWS execution

## Status

Accepted (updated for zero-cost hard constraint)

## Context

The original build specification described disposable AWS validation. A later
project-wide constraint makes **zero monetary cost** a hard requirement for
Definition of Done: the project must be completable and defensible without
spending money, and Free Tier must not be treated as “free.”

These goals must coexist with:

- Keeping real AWS-shaped Terraform in the repository (IaC depth matters).
- Not weakening engineering rigor merely to avoid cloud bills.
- Never claiming AWS deployment that did not happen.

## Decision

### Required path ($0)

- Local FastAPI + SQLite + Docker Compose.
- Terraform `fmt` / `validate` / tflint / module and configuration tests.
- OPA/Conftest against plan JSON fixtures and controlled inventory fixtures.
- Terraform command adapter tested with fixtures / local backends.
- Saved plan **hash binding** verified without cloud apply.
- DNS/TCP verification tested with injectable doubles / local endpoints.
- GitHub Actions: fmt, validate, lint, unit, policy, fixture plan evaluation.
  No AWS credentials. No cloud deploy.

### Optional path (not DoD)

- Real AWS `plan`/`apply` in an operator-owned account.
- Live Route 53 / SG inventory reconciliation.
- GitHub Environment approval gating a real deploy workflow.

Optional results may be documented **only when actually executed**.

### Inventory honesty (DNS and CIDR)

| Path | Behavior |
|---|---|
| Required local/CI | Requested config + **controlled inventory fixtures** + plan JSON |
| Optional AWS | Query/reconcile authoritative cloud state before apply |

Do not pretend OPA alone knows live infrastructure.

### Change specification boundary

`API request → domain model → normalized change specification → Terraform
inputs / module composition`

No arbitrary HCL from user-supplied strings in any path.

### Claim hygiene

Distinguish in README/docs:

1. Implemented and locally validated
2. Terraform defined and statically validated
3. Optionally cloud validated

## Consequences

### Positive

- Fully defensible portfolio project at $0.
- IaC and control-plane depth preserved via static + local rigorous tests.
- No pressure to leave billable resources running for screenshots.

### Negative

- Live AWS behavior is not proven unless someone opts in (accepted).
- Resume/README must not overclaim deployment.

## Related

- ADR-0001 (state roots; config for all envs; no required provision)
- ADR-0002 (saved plan hash — required locally)
- `docs/cost.md`
- `BUILD_PLAN.md` §0
