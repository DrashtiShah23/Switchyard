# ADR-0003: Local-first execution vs explicit AWS validation

## Status

Accepted

## Context

The specification requires:

- Ordinary development without paid AWS.
- Real AWS validation for Definition of Done.
- CI policy evidence.
- Cost discipline.

These goals conflict if every PR performs a live AWS `terraform plan`, or if
mocks are used to claim AWS integration is complete.

## Decision

### Local / PR path (default)

- API and unit tests use fixtures and a mocked Terraform command adapter where
  appropriate.
- Persistence is **SQLite** behind a repository interface (no PostgreSQL for
  appearance).
- CI on every pull request **always** runs: format, validate, lint, unit
  tests, policy tests, and **fixture-based plan evaluation**.
- CI on pull requests does **not** require AWS credentials and does **not**
  apply infrastructure.

### Explicit AWS path

- Real AWS-backed plan/apply runs only on an **explicitly triggered**
  integration/deployment workflow.
- Authoritative human approval for real deploy: **GitHub Environment**.
- Provision **dev only** for the portfolio demonstration.
- Sandbox shape is locked: **single-AZ, no NAT Gateway, short-lived,
  destroy the same day**. Prefer ALB fixed-response over EC2 targets.
- Do not expand the demo into multi-AZ “production-grade” networking. The
  goal is validating the control plane.

### Inventory honesty (DNS and CIDR)

OPA evaluating plan JSON cannot magically know live Route 53 or all existing
security group rules unless that inventory is supplied.

| Path | DNS duplicate / CIDR overlap behavior |
|---|---|
| Local / CI | Validate against requested configuration and a **controlled inventory fixture** (and plan JSON). |
| Real AWS integration | **Query or reconcile** against authoritative infrastructure state (e.g. Route 53) before apply. |

Document this distinction in policy docs and demos. Do not pretend OPA alone
knows current infrastructure.

### Change specification boundary

Regardless of execution mode:

`API request → domain model → normalized change specification → Terraform
inputs / module composition`

The API never constructs arbitrary HCL from user-supplied strings.

## Consequences

### Positive

- Developers can iterate without a bill.
- Policy evidence is reproducible in CI via fixtures.
- AWS validation remains real when it runs (mocks do not satisfy AWS
  acceptance criteria).
- Cost and scope stay intentionally small.

### Negative

- PR CI does not by itself prove live AWS plan success (accepted; proven on
  the explicit workflow and Milestone 16).
- Maintainers must keep inventory fixtures and live reconciliation logic
  aligned with documented limits.

## Related

- ADR-0001 (state roots; config for all envs, provision `dev` only)
- ADR-0002 (saved plan hash on the real apply path)
- `docs/cost.md`
