# Switchyard Build Plan

This document is the engineering plan derived from `SWITCHYARD_BUILD_SPEC.md`.
It is a requirements-driven design, not a literal copy of the specification's
suggested code or layout.

**Status:** approved  
**Current milestone:** Milestone 1 complete — stop for review before Milestone 2  
**AWS validation shape (locked):** single-AZ, no NAT Gateway, short-lived
resources destroyed the same day. Do not expand into multi-AZ “production-like”
topology for the portfolio demonstration.

---

## 0. Approved Decisions (locked)

These decisions supersede earlier proposals where they differ.

1. **State isolation:** Separate Terraform state roots for `dev`, `staging`, and
   `prod`. Do **not** use workspaces.
2. **State locking:** S3 native lockfile only. Do **not** introduce DynamoDB
   solely for locking.
3. **Request → Terraform boundary:**
   `API request → domain model → normalized change specification → Terraform
   inputs / module composition`. The API must never construct arbitrary HCL from
   user-supplied strings.
4. **Human approval:** GitHub Environment approval is the **authoritative**
   human approval boundary for real infrastructure deployment. The API may
   expose `awaiting_approval` as workflow state only. Do **not** build a second
   independent approval system into the API.
5. **Duplicate DNS detection:** Distinguish static/fixture checks from live
   inventory. Local policy tests may use a controlled inventory fixture. Real
   AWS validation must query or reconcile against authoritative Route 53 state
   before apply. Document the distinction; do not pretend OPA alone knows
   current infrastructure.
6. **CIDR overlap:** Same principle—validate against requested configuration
   and known managed inventory locally; use authoritative infrastructure state
   on the real integration path.
7. **Environments:** All three environments have real Terraform configuration
   and isolated state design. Only **dev** is provisioned for the portfolio
   demonstration. Do not create paid staging/production infrastructure merely
   to prove separation.
8. **CI:** Every PR always runs fmt, validate, lint, unit tests, policy tests,
   and fixture-based plan evaluation. A real AWS-backed plan belongs to an
   **explicitly triggered** integration/deployment workflow—not every PR.
9. **Persistence:** SQLite is acceptable. Keep persistence behind a repository
   interface so PostgreSQL could replace it later without rewriting domain
   logic. Do **not** add PostgreSQL merely for appearance.
10. **Saved plan guarantee (core property):** Record the plan artifact hash and
    verify it immediately before apply. This is mandatory architecture, not an
    optional enhancement.

---

## 1. Architecture Intent

Switchyard is a narrow **network change control plane**. Application engineers
submit typed requests for four approved capabilities. The control plane owns
validation, rendering, planning, policy gating, human approval (via GitHub
Environments for real deploys), exact-plan apply, post-apply verification, and
audit. Callers never submit raw HCL or arbitrary Terraform CLI arguments.

### Control flow (intended)

```text
Caller
  -> FastAPI (authn + idempotency)
  -> Domain validation (typed change models)
  -> Normalized change specification
  -> Terraform renderer (module composition / typed inputs — never raw user HCL)
  -> terraform plan  -> saved binary plan + plan JSON + artifact hash
  -> OPA/Conftest on plan JSON (+ inventory fixtures locally)
  -> State: awaiting_approval (API workflow marker only)
  -> GitHub Environment approval (authoritative for real deploy)
  -> Verify plan artifact hash
  -> terraform apply of the exact saved plan
  -> DNS / TCP (/ optional HTTPS) verification
  -> Audit + metrics + durable request history
```

### Design principles

1. **Safe product API, not a Terraform proxy.** HTTP handlers validate and
   persist; orchestration lives in services behind interfaces.
2. **Deterministic, reviewable infrastructure.** Every apply consumes a
   previously reviewed saved plan artifact whose hash is verified immediately
   before apply; apply must not regenerate a plan.
3. **Policy before mutation.** OPA evaluates plan JSON, not raw HCL, and is
   honest about what requires live inventory.
4. **Local-first development.** Default `make` / compose path uses fixtures
   and mocked Terraform execution. Real AWS is an explicit validation lane.
5. **Cheap, disposable AWS proof.** Single-AZ, no NAT, short-lived; destroy is
   first-class. Validating the control plane is the goal—not simulating Box-scale
   production networking.
6. **Evidence over assertion.** README claims must come from tests, CI
   artifacts, or exercised runs. No invented metrics or hardcoded “green”
   results.

### Major architectural decisions (with reasons)

| Decision | Choice | Reason |
|---|---|---|
| Env isolation | **Separate state roots** per `dev` / `staging` / `prod` (not workspaces) | Clear blast-radius boundaries, independent locking, simpler IAM and backend config. ADR-0001. |
| State locking | **S3 native lockfile** (`use_lockfile = true`) | Current supported mechanism; DynamoDB not required solely for locking. |
| Change pipeline | **Typed change specification** between domain and Terraform | Prevents arbitrary HCL from API input; keeps a reviewable intermediate artifact. |
| Approval | **GitHub Environment** authoritative; API `awaiting_approval` is state only | One approval system for real deploys; avoid dual control-plane approval UX. |
| DNS / CIDR checks | **Fixture inventory locally; authoritative AWS state on real path** | Honest about OPA limits; still catches unsafe patterns in CI. |
| Env provisioning | **Config for all three; provision only `dev` for demo** | Proves isolation without paying for staging/prod. |
| Local persistence | **SQLite behind repository interface** | Sufficient for demo; swappable without domain rewrites. |
| Local Terraform | **Command adapter + fixtures** | Ordinary development never requires AWS. |
| Auth (demo) | **Static API keys / bearer tokens** from env | Spec asks for local demonstration auth, not a full IdP. |
| TLS scope | **Certificate reference / attachment** (ACM ARN) | Matches “attachment or reference”; ACM issuance optional on E2E. |
| ALB demo shape | **Fixed-response** where possible; **single-AZ; no NAT** | Control-plane validation without EC2/NAT cost. |
| CI plan strategy | **Always:** fmt, validate, tflint, unit, policy, fixture plan eval. **Explicit workflow:** real AWS plan/apply. | Cost discipline without weakening policy evidence. |
| Saved plan | **Hash recorded + verified pre-apply** | Core safety property. ADR-0002. |

---

## 2. Major Components and Responsibilities

### API service (`app/api`, `app/main.py`)

- Accept change requests for DNS, LB routes, TLS binding, SG rules.
- Authenticate demo callers; enforce idempotency keys on create.
- Expose request status, plan, policy, and verification views.
- Represent `awaiting_approval` as workflow state only—no independent approve API
  that bypasses GitHub Environments for real deploys.
- Own HTTP concerns only; no Terraform orchestration in handlers.

### Domain layer (`app/domain`)

- Typed models: DNS record, LB route, TLS binding, SG rule, environment,
  change request, **normalized change specification**, plan/policy/verification
  results, lifecycle states.
- Pure validation and state-transition rules.
- Provider details stay out of domain types where practical.

### Application services (`app/services`)

- Orchestrate: validate → normalize change spec → render → plan → policy →
  awaiting_approval → (external approval) → hash verify → apply → verify.
- Enforce lifecycle transitions and failure marking.
- Coordinate idempotency and duplicate-intent protection.

### Repositories (`app/repositories`)

- Persist requests, plan artifact metadata (**including hash**), policy outcomes,
  verification results, audit events.
- Abstract storage so SQLite can later become Postgres without rewriting
  domain or orchestration logic.

### Terraform adapter (`app/infrastructure`)

- Accept **normalized change specifications** only; render module composition /
  typed variable inputs (never concatenate user strings into HCL).
- Run `terraform` via controlled argv (never user-supplied shell text).
- Produce saved plan binary, plan JSON, and **artifact hash**.
- Apply **only** after hash verification against the recorded identity.

### Policy layer (`policy/`)

- Conftest/OPA policies against Terraform plan JSON.
- Local tests may inject controlled inventory fixtures for DNS/CIDR cases.
- Real AWS path reconciles against authoritative inventory before apply.
- ≥30 seeded denied fixtures with clear “which policy blocked this” reporting.

### Verification (`app/verification`, `scripts/verify_*.py`)

- DNS resolution, TCP connect, optional HTTPS + cert/status checks.
- Bounded retries/backoff; failures mark deployment unhealthy with actionable
  output.

### Observability (`app/observability`)

- Structured logs with the required correlation fields.
- Prometheus-compatible `/metrics` for the minimum counters/histograms.

### CI/CD (`.github/workflows`)

- PR: fmt, validate, lint, unit tests, policy tests, fixture-based plan
  evaluation; never auto-apply; **no required live AWS plan on every PR**.
- Deploy / integration (explicitly triggered): protected GitHub Environment
  approval, download exact plan, **verify artifact hash**, apply, verify,
  persist result.

### Terraform modules (`terraform/modules`)

- `network`, `security_group`, `alb`, `listener_rule`, `dns`, `tls`
- Typed variables, validation blocks, outputs, descriptions, pinned versions,
  examples; tests where practical.

### Bootstrap / environments (`terraform/bootstrap`, `terraform/environments`)

- State bucket + locking configuration once.
- Isolated `dev` / `staging` / `prod` roots with remote state (config for all;
  provision `dev` only for demo).

---

## 3. Hardest Technical and Operational Risks

| Risk | Why it is hard | Mitigation |
|---|---|---|
| **Exact plan binding** | Easy to accidentally re-plan at apply time | Store SHA-256 of plan artifact; verify immediately before apply; tests assert apply uses saved plan only. |
| **Concurrent changes / state lock** | Two requests can race on one state root | Serialize applies per environment in the service; surface lock errors as first-class failures; document operator retry. |
| **Policy vs live inventory** | OPA cannot see Route 53 / SG state it was not given | Fixture inventory in local tests; authoritative AWS queries on real path; document the split clearly. |
| **DNS propagation flakiness** | Apply success ≠ immediate resolution | Bounded retry/backoff; distinct `verifying` state; unhealthy on timeout with actionable detail. |
| **CI without AWS vs real plan** | Live AWS plan costs credentials and money | Fixture plan evaluation always on PR; real AWS plan only on explicit integration/deploy workflow. |
| **Cost blowups (ALB, NAT, idle resources)** | ALB is the main recurring cost; multi-AZ/NAT is tempting scope creep | **Locked:** single-AZ, no NAT, short-lived sandbox, same-day destroy. |
| **Rollback asymmetry** | DNS, listener rules, and SG rules roll back differently | Document per-capability rollback; prefer additive reversible changes in demos. |
| **Over-scoping** | Temptation to add HA, LocalStack, Postgres, multi-cloud, etc. | Explicit non-goals; reject impressive-but-empty tech. |

---

## 4. Spec Ambiguities — Resolutions

| Topic | Resolution |
|---|---|
| How requests become Terraform | Typed intermediate **change specification**; renderer emits module inputs/composition only. |
| Human approval | GitHub Environment is authoritative for real deploy; API `awaiting_approval` is workflow state only. |
| Authentication | Bearer API keys for local demo; no Cognito unless later requested. |
| Duplicate DNS | Static/fixture checks locally; Route 53 reconciliation on real AWS path; document limits. |
| CIDR overlap | Requested config + managed inventory locally; authoritative state on real path. |
| Repository root | Repo root is the project root (no nested `switchyard/` wrapper). |
| PR live Terraform plan | Not on every PR. Fixture-based plan evaluation always; AWS-backed plan on explicit workflow. |
| Three AWS environments | Config + state design for all three; provision only `dev` for demo. |
| State locking | S3 native lockfile; no DynamoDB for locking. |
| Persistence | SQLite behind repository interface; no Postgres for show. |

### Explicit non-goals (keep scope intentional)

- Multi-cloud providers
- Multi-AZ / NAT Gateway “production” networking for the demo
- Full service mesh / VPC lattice / PrivateLink productization
- General IAM / compute / database provisioning
- Multi-tenant SaaS control plane
- Replacing Atlantis/Spacelift/TFC for all org Terraform
- Guaranteed automated rollback across all resource types
- Second independent API approval system for real infrastructure
- PostgreSQL (or other heavy deps) added only for appearance
- LocalStack as the default development path

---

## 5. Final Repository Structure

```text
.
├── README.md
├── LICENSE
├── BUILD_PLAN.md
├── SWITCHYARD_BUILD_SPEC.md
├── Makefile
├── pyproject.toml
├── docker-compose.yml
├── .env.example
├── .gitignore
├── .github/
│   └── workflows/                # added in later milestones
├── app/
│   ├── __init__.py
│   ├── main.py                   # stub until Milestone 3
│   ├── api/
│   ├── domain/
│   ├── services/
│   ├── repositories/
│   ├── infrastructure/
│   ├── verification/
│   └── observability/
├── terraform/
│   ├── bootstrap/
│   ├── modules/                  # modules land in M4–M6
│   ├── environments/
│   │   ├── dev/
│   │   ├── staging/
│   │   └── prod/
│   └── tests/
├── policy/
│   ├── terraform/
│   └── tests/
│       ├── allowed/
│       └── denied/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
├── scripts/
├── docs/
│   ├── architecture.md
│   ├── threat_model.md
│   ├── operations.md
│   ├── demo.md
│   ├── cost.md
│   └── adr/
│       ├── 0001-environment-state-isolation.md
│       ├── 0002-saved-plan-apply-binding.md
│       └── 0003-local-vs-aws-execution.md
└── examples/
    └── requests/
```

---

## 6. Ordered Milestones and Acceptance Criteria

Each milestone should end in **one coherent commit** (or a small series of
coherent commits if a milestone is large), with formatting, lint, and tests
green for whatever exists at that point. **Stop after each milestone’s
validation unless explicitly told to continue.**

### Milestone 0 — Plan accepted

**Acceptance**

- [x] `BUILD_PLAN.md` reviewed; decisions in §0 locked.
- [x] No application code required for this milestone.

### Milestone 1 — Repository skeleton and ADRs

**Deliver**

- License, `.gitignore`, `Makefile` stubs, `pyproject.toml` skeleton,
  `docker-compose.yml` stub, `.env.example`, docs stubs, ADR-0001/0002/0003.

**Acceptance**

- [x] Fresh clone shows understandable layout matching §5.
- [x] ADRs explain state roots vs workspaces, saved-plan binding, and
      local-vs-AWS execution (including inventory honesty and cost shape).
- [x] `make help` lists intended targets.

### Milestone 2 — Domain models and validation

**Deliver**

- Domain types for four change kinds, environments, lifecycle states,
  normalized change specification, validation rules, state transition helpers.
- Unit tests for validation and illegal transitions.

**Acceptance**

- [ ] Invalid DNS/LB/TLS/SG inputs rejected with clear errors.
- [ ] Lifecycle transitions enforced in domain tests (no handler logic yet).
- [ ] Change specification is a distinct typed artifact (not raw HCL).

### Milestone 3 — FastAPI change request API (persistence + status)

**Deliver**

- Endpoints: `POST /v1/changes`, `GET /v1/changes/{id}`, plan/policy/verification
  stubs, `GET /health`.
- Idempotency keys; SQLite behind repository interface; demo auth; request IDs.
- No independent approve-for-apply API for real infrastructure.

**Acceptance**

- [ ] Create returns stable `request_id`; duplicate idempotency key returns the
      same logical request.
- [ ] Handlers contain no Terraform subprocess calls and do not build HCL from
      user strings.
- [ ] Unit/API tests cover auth failure, validation failure, happy create/get.

### Milestone 4 — Terraform module foundation (network + shared patterns)

**Deliver**

- Version-pinned AWS provider pattern; `network` module with typed variables,
  validation, outputs, example; environment root skeletons for all three envs.

**Acceptance**

- [ ] `terraform fmt -check` and `terraform validate` succeed for the module
      (local backend / no paid resources required).
- [ ] No environment-specific constants embedded in modules.
- [ ] Network module defaults assume single-AZ-capable composition (no NAT).

### Milestone 5 — Security group + DNS modules

**Deliver**

- `security_group` and `dns` modules with validation/outputs/examples.
- Domain → change spec → render path for SG and DNS (mock executor OK in app tests).

**Acceptance**

- [ ] Module input validation rejects obviously unsafe defaults where
      expressible in Terraform `validation` blocks.
- [ ] Renderer produces deterministic composition inputs from change specs.

### Milestone 6 — ALB + listener rule + TLS modules

**Deliver**

- `alb`, `listener_rule`, `tls` (reference/attachment) modules.
- Remaining change types wired through renderer.

**Acceptance**

- [ ] All four request types can be rendered to Terraform inputs.
- [ ] Modules expose outputs needed for cross-stack references and verification.
- [ ] ALB examples prefer fixed-response; no required EC2 targets for demo path.

### Milestone 7 — Terraform command adapter + plan artifacts

**Deliver**

- Adapter: plan → save binary + JSON + **hash**; show; apply-from-saved-plan
  with pre-apply hash verification.
- Unit tests with injected command runner (mocks OK here).

**Acceptance**

- [ ] Apply path refuses to run without a saved plan path.
- [ ] Plan identity (hash) stored on the request record.
- [ ] Mismatched hash is rejected before apply.
- [ ] No user-controlled arbitrary Terraform flags.

### Milestone 8 — Remote state, bootstrap, environment isolation

**Deliver**

- Bootstrap for S3 backend + native lockfile.
- `dev` / `staging` / `prod` roots with separate backends (provision guidance:
  demo uses `dev` only).
- Cross-stack outputs / `terraform_remote_state` for foundation → edge.

**Acceptance**

- [ ] Three environment roots exist with distinct state keys/prefixes.
- [ ] Docs explain bootstrap and why workspaces were rejected.
- [ ] Cross-stack dependency uses outputs, not copied literals.

### Milestone 9 — OPA/Conftest policy engine

**Deliver**

- Policies for the spec’s rejection categories.
- Allowed + denied fixtures; inventory fixtures where DNS/CIDR need them.
- Docs noting static vs live inventory limits.

**Acceptance**

- [ ] `conftest test` runs locally without AWS.
- [ ] Each policy has at least one allowed and one denied fixture.
- [ ] Failure messages identify the blocking policy.

### Milestone 10 — ≥30 negative policy fixtures

**Deliver**

- Seeded unsafe plan JSON cases across categories; blocker reporting.

**Acceptance**

- [ ] At least thirty denied cases fail for the expected policy.
- [ ] Suite is deterministic in CI; no hardcoded pass documentation.

### Milestone 11 — GitHub Actions PR pipeline

**Deliver**

- `pull_request.yml`: fmt, validate, tflint, unit tests, policy tests,
  fixture-based plan evaluation. No apply. No required live AWS plan.

**Acceptance**

- [ ] PR workflow runs on a clean checkout.
- [ ] Policy / fixture plan evaluation failures fail the job.
- [ ] Workflow does not apply infrastructure and does not require AWS creds.

### Milestone 12 — Approval + saved-plan apply path

**Deliver**

- Deploy/integration workflow with **GitHub Environment** protection.
- Artifact download; **hash verification**; apply exact plan; persist result.
- API may mark `awaiting_approval` but does not own a second approval system.

**Acceptance**

- [ ] Real deploy path requires GitHub Environment approval.
- [ ] Tampered / mismatched plan hash is rejected.
- [ ] Apply job does not silently generate a new plan.

### Milestone 13 — DNS and TCP verification

**Deliver**

- Probes with timeout, bounded backoff, actionable failures; API exposure.

**Acceptance**

- [ ] Unit tests cover retry/failure with injected resolvers/sockets.
- [ ] Verification failure marks request unhealthy/failed appropriately.

### Milestone 14 — Observability and audit history

**Deliver**

- Structured logging; `/metrics`; audit via request history.

**Acceptance**

- [ ] Required log fields present where applicable.
- [ ] Minimum metrics exposed and asserted via endpoint tests.
- [ ] Credentials never logged.

### Milestone 15 — Failure injection tests

**Deliver**

- Lock, plan failure, policy unavailable/rejection, apply failure, DNS delay,
  TCP verify failure, partial dependency failure, duplicate request, retry.

**Acceptance**

- [ ] Each failure mode has an automated test with expected state/outcome.
- [ ] Retries do not create duplicate intent for identical idempotency keys.

### Milestone 16 — AWS end-to-end validation (real resources)

**Deliver**

- Disposable **dev** sandbox only: single-AZ, no NAT, short-lived ALB
  (fixed-response), SG + DNS path through the control plane.
- Real plan → policy → GitHub Environment approval → hash verify → apply →
  verify → **same-day destroy**.
- Live Route 53 / inventory reconciliation for DNS (and CIDR where applicable).

**Acceptance**

- [ ] Executed against real AWS (not mocks); evidence recorded from the run.
- [ ] Post-apply DNS and TCP verification exercised.
- [ ] Staging/prod AWS resources were not provisioned for the demo.
- [ ] Destroy completed (or residual free leftovers documented, e.g. empty state bucket).
- [ ] No invented metrics.

### Milestone 17 — Documentation and demo polish

**Deliver**

- Public README (Mermaid, capabilities, real CI/fixture policy evidence,
  limitations, cost notes), architecture, threat model, operations, demo.

**Acceptance**

- [ ] Another engineer can run local demo from README alone.
- [ ] Senior-review questions answered in ADRs/docs.
- [ ] No job-application framing; no fabricated benchmarks.

---

## 7. Local vs AWS Milestones

| Milestone | Entirely local? | Notes |
|---|---|---|
| 0 Plan | Yes | Done |
| 1 Skeleton + ADRs | Yes | |
| 2 Domain | Yes | |
| 3 API + SQLite | Yes | |
| 4–6 Terraform modules | Mostly local | fmt/validate/test without paid apply |
| 7 Adapter | Yes | Mocks for unit tests |
| 8 Remote state design | Config local; bucket bootstrap needs AWS when first created | |
| 9–10 Policy | Yes | Plan JSON + inventory fixtures |
| 11 PR CI | Yes | No AWS required |
| 12 Approval/apply path | Workflow+logic local; real apply needs AWS | |
| 13 Verification | Unit local; real DNS/TCP needs deployed resources | |
| 14 Observability | Yes | |
| 15 Failure tests | Yes | |
| 16 AWS E2E | **Requires real AWS (`dev` only)** | Single-AZ, no NAT, destroy same day |
| 17 Docs | Yes | May embed M16 artifacts |

---

## 8. Cheapest Credible AWS Validation Path (locked)

### Constraints (do not “improve” away)

- Single Availability Zone
- No NAT Gateway
- No multi-AZ ALB “HA” topology for the demo
- Short-lived resources; destroy the same day
- Provision **dev only**
- Prefer ALB **fixed-response** over EC2 targets
- Goal: validate the **control plane**, not operate production-scale networking

### Billable / potentially billable resources

| Resource | Why needed | Cost risk | Discipline |
|---|---|---|---|
| S3 state bucket | Remote state + lockfile | Very low | Optional retain empty; or destroy |
| VPC + subnets (single AZ) | Foundation | Free | No NAT |
| Security groups | Core capability | Free | |
| Application Load Balancer | Listener/route proof | **Primary cost** | Same-day destroy |
| Listener rules / fixed-response | Route proof without EC2 | With ALB | Prefer fixed-response |
| Route 53 hosted zone | DNS proof | Low if short-lived | Destroy or reuse existing zone briefly |
| ACM certificate | Optional TLS path | Free (public) | Optional for first E2E |
| EC2 / NAT / RDS / ECS / multi-AZ | Not required | Avoid | Out of scope |

---

## 9. Mapping Resume Claims → Evidence

| Claim | Evidence source |
|---|---|
| FastAPI for DNS/LB/TLS/SG requests | API + unit/contract tests; example requests |
| Versioned Terraform modules with validation | Modules + validate/tests in CI |
| Isolated envs + remote state | `environments/*` + bootstrap + ADR-0001; `dev` provisioned in M16 |
| Cross-stack via outputs | Edge stack remote state; docs |
| CI fmt/validate/lint/policy + fixture plan eval | `pull_request.yml` logs |
| Unsafe changes rejected | ≥30 denied fixtures + CI policy job output |
| Only reviewed saved plan applied | Deploy workflow + **hash verification** + tests |
| Post-apply DNS/TCP verification | Verification tests + AWS E2E artifacts |
| ≥30 unsafe suite | `policy/tests/denied` + reporter |

---

## 10. Proposed Commit Cadence (Git History)

1. `docs: add build plan and repository skeleton with ADRs`
2. `feat(domain): add change models, validation, and lifecycle transitions`
3. `feat(api): add change request API with idempotency and persistence`
4. `feat(terraform): add network module and environment skeletons`
5. `feat(terraform): add security group and DNS modules`
6. `feat(terraform): add ALB, listener rule, and TLS modules`
7. `feat(infra): add Terraform plan/apply adapter with plan identity`
8. `feat(terraform): add S3 backend bootstrap and env state isolation`
9. `feat(policy): add OPA/Conftest policies for plan JSON`
10. `test(policy): add thirty-plus denied infrastructure fixtures`
11. `ci: add pull request fmt validate lint test and policy workflow`
12. `feat(deploy): bind GitHub Environment approval to exact saved plan apply`
13. `feat(verify): add DNS and TCP post-apply verification`
14. `feat(obs): add structured audit logs and metrics`
15. `test: add failure injection coverage for control plane paths`
16. `docs: record AWS sandbox validation evidence and destroy procedure`
17. `docs: polish README, architecture, threat model, and demo`

---

## 11. Deferred / optional questions

Resolved items are in §0. Still optional when reaching M16:

1. **Route 53:** Create a short-lived hosted zone in the sandbox, or reuse an
   existing personal zone/subdomain?
2. **TLS in first AWS E2E:** Certificate ARN reference only, or include ACM
   issuance in the first pass?

---

## 12. Stop discipline

After each milestone: validate acceptance criteria, then **stop** until told to
continue. Do not batch multiple milestones without approval.
