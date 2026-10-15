# ADR-0001: Environment state isolation via separate state roots

## Status

Accepted

## Context

Switchyard must isolate development, staging, and production infrastructure
state. Terraform offers two common approaches:

1. **Workspaces** — one backend configuration, multiple workspace-named state
   objects.
2. **Separate state roots** — distinct backend configurations (bucket prefix
   and/or key) per environment, usually with separate root modules under
   `terraform/environments/{dev,staging,prod}`.

The build specification requires environment isolation and remote state, and
asks for an explicit tradeoff decision.

## Decision

Use **separate Terraform state roots** for `dev`, `staging`, and `prod`.
**Do not use Terraform workspaces** for environment separation.

Additionally:

- All three environments have real Terraform configuration and isolated
  backend design in the repository.
- **No environment must be provisioned in AWS for Definition of Done**
  (zero-cost hard constraint). Live provision remains optional and
  operator-owned.
- Do not create paid staging or production infrastructure merely to prove
  that environment folders exist.

## Consequences

### Positive

- Blast radius is obvious: wrong-env applies require pointing at a different
  root, not flipping a workspace name.
- Locking, IAM, and backend keys are independently reviewable per environment.
- Cross-stack references can be explicit (`terraform_remote_state` to a known
  state key) without workspace interpolation tricks.
- Matches how many platform teams actually separate prod from non-prod.

### Negative

- Some duplication of root-module wiring across environment directories
  (mitigated with shared modules).
- Operators must be disciplined about which directory they run from
  (documented in operations runbooks).

### Rejected alternative: workspaces

Workspaces share a backend configuration and are easy to misuse (`terraform
workspace select prod` from muscle memory). They obscure ownership for a
control plane that already models `environment` as a first-class domain
concept. The minor DRY benefit does not outweigh the operational clarity loss
for this project.

## Related

- ADR-0003 (zero-cost local validation vs optional AWS)
- `docs/cost.md`
