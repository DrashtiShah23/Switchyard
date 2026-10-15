# Operations

> Stub for Milestone 1.

## Local

```bash
make help
make up      # wired in Milestone 3+
make down
make test   # wired as suites land
```

Persistence defaults to SQLite behind a repository interface. Do not introduce
PostgreSQL solely for appearance.

## CI

Pull requests always run formatting, validation, lint, unit tests, policy
tests, and fixture-based plan evaluation. They do **not** require live AWS
credentials and must not apply infrastructure.

Real AWS-backed plan/apply runs only on an explicitly triggered
integration/deployment workflow with GitHub Environment approval.

## AWS sandbox (dev only)

Constraints (locked):

- Single Availability Zone
- No NAT Gateway
- Short-lived resources; destroy the same day
- Do not provision paid staging/production infrastructure for the demo

```bash
make destroy-sandbox   # wired in Milestone 16
```

## Saved plan apply

Before apply, verify the recorded plan artifact hash. Mismatch is a hard
failure. See [ADR-0002](adr/0002-saved-plan-apply-binding.md).
