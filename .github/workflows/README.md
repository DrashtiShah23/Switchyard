# GitHub Actions

Workflows land in later milestones:

- `pull_request.yml` (Milestone 11) — fmt, validate, lint, unit tests, policy
  tests, fixture-based plan evaluation. No apply. No required live AWS plan.
- `deploy.yml` (Milestone 12) — explicitly triggered; GitHub Environment
  approval; verify saved plan hash; apply exact plan; verify.
