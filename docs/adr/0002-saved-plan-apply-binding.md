# ADR-0002: Exact saved plan apply binding via artifact hash

## Status

Accepted

## Context

A common failure mode in Terraform automation is:

1. Humans (or CI) review Plan A.
2. Apply silently runs `terraform plan` again and applies Plan B.

Between A and B, state, variables, provider behavior, or concurrent changes
can diverge. The reviewed artifact is then not what mutated infrastructure.

Switchyard’s resume claims and senior-review bar require proving that **only a
reviewed saved plan may be applied**.

## Decision

Treat exact saved-plan binding as a **core architectural property**:

1. After a successful `terraform plan -out=<file>`, persist:
   - the plan binary (or CI artifact thereof)
   - plan JSON (`terraform show -json`)
   - a **cryptographic hash** of the plan artifact (SHA-256)
2. Record that hash on the change request.
3. Immediately before `terraform apply`, recompute the hash of the artifact
   about to be applied and **refuse to proceed on mismatch**.
4. Apply using the saved plan file only (`terraform apply <planfile>`).
   Do not regenerate a plan in the apply path.

Human approval for real infrastructure deployment is provided by a **GitHub
Environment** protection rule. The API may show `awaiting_approval` as
workflow state but does not implement a second independent approval system.

## Consequences

### Positive

- Reviewers can reason about a concrete artifact identity.
- Tampering or accidental substitution fails closed.
- Aligns CI deploy workflow with control-plane safety guarantees.
- Small detail, large signal: this is how careful infrastructure automation
  behaves.

### Negative

- Plan artifacts must be stored and retrieved reliably (local artifact dir
  and/or CI artifacts).
- Operators cannot “just re-plan and apply” on the deploy path without
  starting a new change request — by design.

### Non-negotiable tests

- Apply without a saved plan path fails.
- Apply with a mismatched hash fails.
- Apply argv does not invent a new plan.

## Related

- ADR-0003 (when real apply runs)
- Milestone 7 (adapter) and Milestone 12 (deploy workflow)
