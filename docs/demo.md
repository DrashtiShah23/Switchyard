# Demo

> Replace stubs with reproducible steps and captured artifacts as milestones
> complete. Do not invent results. Label evidence using the classes in
> `docs/cost.md`.

## Local (required)

1. Start the API (`make up` — Milestone 3+).
2. Submit an example request from `examples/requests/`.
3. Observe validation → change specification → plan/policy path.
4. Inspect request status via the API.

Milestone 2 currently demonstrates domain validation and lifecycle locally via:

```bash
pytest tests/unit -q
```

## Optional AWS

Not required for Definition of Done. If an operator runs a real AWS path in
their own account, record it only when it actually happened, and destroy any
created resources promptly.
