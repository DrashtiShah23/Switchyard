# Operations

## Local (required path)

```bash
make help
make up      # wired in Milestone 3+
make down
make test
```

Persistence defaults to SQLite behind a repository interface.

Ordinary validation never requires AWS credentials or billable resources.

## CI (required path)

Pull requests run formatting, validation, lint, unit tests, policy tests, and
fixture-based plan evaluation. They must not apply infrastructure and must not
require AWS credentials.

## Saved plan apply

Before apply, verify the recorded plan artifact hash. Mismatch is a hard
failure. See [ADR-0002](adr/0002-saved-plan-apply-binding.md).

Required DoD proves this with local/mock backends.

## Optional AWS

Cloud apply is operator-owned and not part of Definition of Done. See
[cost.md](cost.md). Never document optional cloud results as if they were
required, and never claim deployment that did not run.
