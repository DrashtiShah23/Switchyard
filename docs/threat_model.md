# Threat model

> Stub for Milestone 1. Expand with trust boundaries and abuse cases as the
> API and deploy path land.

## Trust boundaries (planned)

| Boundary | Trust assumption |
|---|---|
| API caller → API | Authenticated with demo API keys; not a full IdP |
| API → Terraform adapter | No user-controlled shell or arbitrary Terraform flags |
| Plan artifact → Apply | Hash must match; apply must not regenerate a plan |
| Human approval | GitHub Environment for real deploy; not a second API approval system |
| Policy engine | Evaluates plan JSON; inventory honesty documented for DNS/CIDR |

## Abuse cases to cover later

- Submitting raw HCL or Terraform arguments through API fields
- Tampering with a saved plan after review
- Applying without GitHub Environment approval
- Open administrative ingress / wildcard SG rules
- Duplicate DNS ownership / environment boundary violations
- Logging credentials or private key material

## Non-goals

This document does not claim that OPA alone knows live Route 53 or security
group inventory. See ADR-0003 for the static vs authoritative inventory split.
