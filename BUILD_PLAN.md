# Switchyard Build Plan

This document is the engineering plan derived from `SWITCHYARD_BUILD_SPEC.md`.
It is a requirements-driven design, not a literal copy of the specification's
suggested code or layout.

**Status:** approved (including zero-cost constraint and git ownership rule)  
**Current milestone:** Milestone 5 complete — stop for owner commit handoff before Milestone 6  
**Git ownership:** human operator only — agents never commit or push

---

## 0a. Permanent rule: human-only Git ownership

**The human repository owner is the only person allowed to create Git commits
or push changes.** This rule is permanent and overrides any earlier
BUILD_PLAN / BUILD_SPEC language that suggested the agent should commit after
milestones.

### Agents may

- Inspect `git status`, `git diff`, and `git log`
- Create, modify, and delete files required by approved implementation
- Run tests, formatting, linting, type checking, and validation
- Suggest commit boundaries and commit messages

### Agents must never run

- `git commit`
- `git push`
- `git merge`
- `git rebase`
- `git tag`
- `git reset --hard`
- `git clean`
- `git checkout` / `git restore` commands that discard changes
- `git add` unless the owner **explicitly** requests it

### End-of-milestone handoff (mandatory)

After finishing a milestone’s implementation and validation, the agent must:

1. **Stop** before staging or committing anything.
2. Show validation results.
3. Show a concise summary of `git diff`.
4. List all files created, modified, or deleted.
5. Separate changes into logical commit groups when more than one commit is
   appropriate.
6. Give the exact suggested commit message for each group.
7. Give the exact git commands the owner can run themselves.
8. **Wait** for the owner to confirm they committed before starting the next
   milestone.

Never interpret “finish the milestone”, “proceed”, “continue”, or similar
language as permission to commit.

---

## 0. Hard constraint: zero cost

**Zero monetary cost is a hard architectural requirement for Definition of Done.**

The project must be completable and fully defensible without spending any money.
Do not assume AWS Free Tier makes a resource free. If a cloud action can
potentially generate a charge, it must **not** be required for any milestone
acceptance criterion or for Definition of Done.

### Evidence classes (use these consistently in docs / README / resume)

| Class | Meaning | Allowed claim |
|---|---|---|
| **Implemented and locally validated** | Code + tests ran on a developer machine or free CI | “Validated locally / in CI” |
| **Terraform defined and statically validated** | Modules/envs exist; `fmt`, `validate`, tflint, tests, policy/fixtures | “Infrastructure designed and statically validated” |
| **Optionally cloud validated** | Someone ran a real AWS path outside required DoD | Only if it **actually** ran; never implied |

Never claim something was deployed to AWS unless it actually was.
Never convert Terraform configuration into a false deployment claim.

### Default (required) validation path — $0

- `terraform fmt` / `validate` / tflint
- Module and configuration tests
- OPA/Conftest policy evaluation
- Plan **fixture** based tests (committed plan JSON)
- Python unit / integration / failure-injection tests
- Local Docker / Docker Compose reproducing architecture and failure behavior
- GitHub Actions within free-usage assumptions; **no cloud deployment**

### Optional validation path — not required for DoD

- Real AWS plan/apply against a caller-owned account
- Must remain documented as optional
- Must never be the only way to satisfy an acceptance criterion
- Must not create required billable resources in the default workflow

### Forbidden in any *required* workflow

Do not create as part of required validation:

- ALBs / NLBs
- EC2 instances
- Route 53 hosted zones
- NAT Gateways
- Elastic IPs
- ECS services
- RDS / ElastiCache
- Any other potentially billable cloud resource

AWS Terraform modules and environment configuration **remain in the repository**
because IaC design is core to the project. They are statically validated by
default; live provisioning is optional only.

Engineering depth must **not** be weakened to avoid cloud costs. Replace
cloud-dependent validation with meaningful local integration tests,
infrastructure tests, policy tests, configuration validation, failure
injection, and reproducible local benchmarks.

---

## 1. Approved Decisions (locked)

These decisions supersede earlier proposals where they differ.

1. **Human-only Git ownership:** Agents never commit or push; owner alone
   owns history. (§0a)
2. **Zero cost DoD:** No milestone requires paid AWS (or any paid cloud) to
   satisfy Definition of Done. (§0)
3. **State isolation:** Separate Terraform state roots for `dev`, `staging`, and
   `prod`. Do **not** use workspaces.
4. **State locking:** S3 native lockfile design in Terraform config. Do **not**
   introduce DynamoDB solely for locking. Creating a real state bucket is
   **optional** and not required for DoD (local backends + config review cover
   the required path).
5. **Request → Terraform boundary:**
   `API request → domain model → normalized change specification → Terraform
   inputs / module composition`. The API must never construct arbitrary HCL from
   user-supplied strings.
6. **Human approval:** For optional real infrastructure deployment, GitHub
   Environment approval is the authoritative human boundary. The API may expose
   `awaiting_approval` as workflow state only. Do **not** build a second
   independent approval system into the API. Required DoD proves the approval
   *boundary behavior* via local/CI simulation of the gate.
7. **Duplicate DNS detection:** Local/CI uses controlled inventory fixtures.
   Optional AWS path may reconcile against Route 53. Document the distinction;
   do not pretend OPA alone knows current infrastructure.
8. **CIDR overlap:** Same principle—requested config + managed inventory
   fixtures locally; optional authoritative cloud state only on the optional path.
9. **Environments:** All three environments have real Terraform configuration
   and isolated state **design**. None must be provisioned in AWS for DoD.
10. **CI:** Every PR always runs fmt, validate, lint, unit tests, policy tests,
    and fixture-based plan evaluation. No AWS credentials. No cloud deploy.
11. **Persistence:** SQLite behind a repository interface. Do **not** add
    PostgreSQL merely for appearance.
12. **Saved plan guarantee (core property):** Record the plan artifact hash and
    verify it immediately before apply. Mandatory architecture.

---

## 2. Architecture Intent

Switchyard is a narrow **network change control plane**. Application engineers
submit typed requests for four approved capabilities. The control plane owns
validation, rendering, planning, policy gating, human-approval boundary, exact
plan apply, post-apply verification, and audit. Callers never submit raw HCL or
arbitrary Terraform CLI arguments.

The system is **architecturally credible for AWS** (modules, providers, state
roots, IAM-shaped least privilege docs) while remaining **fully completable at
zero cost** via local execution and static IaC validation.

### Control flow (intended)

```text
Caller
  -> FastAPI (authn + idempotency)
  -> Domain validation (typed change models)
  -> Normalized change specification
  -> Terraform renderer (module composition / typed inputs — never raw user HCL)
  -> terraform plan  -> saved binary plan + plan JSON + artifact hash
       (required path: local terraform and/or committed plan fixtures)
  -> OPA/Conftest on plan JSON (+ inventory fixtures)
  -> State: awaiting_approval (API workflow marker only)
  -> Approval boundary (required: simulated gate; optional real deploy: GitHub Environment)
  -> Verify plan artifact hash
  -> terraform apply of the exact saved plan
       (required path: local/mock backend; optional: real AWS — never required)
  -> DNS / TCP verification
       (required path: local test doubles / compose services; optional: real endpoints)
  -> Audit + metrics + durable request history
```

### Design principles

1. **Safe product API, not a Terraform proxy.**
2. **Deterministic, reviewable infrastructure** via exact saved-plan hash binding.
3. **Policy before mutation** against plan JSON, honest about inventory limits.
4. **Zero-cost by default.** Docker Compose + fixtures + static Terraform checks.
5. **AWS-shaped IaC without required AWS bills.** Modules remain real; apply is optional.
6. **Evidence over assertion.** README/resume claims match what was actually executed.

### Major architectural decisions (with reasons)

| Decision | Choice | Reason |
|---|---|---|
| Cost model | **$0 required DoD** | Project must be completable without spending money. |
| Env isolation | **Separate state roots** (not workspaces) | Clear blast radius; ADR-0001. |
| State locking | **S3 native lockfile in config** | Current mechanism; real bucket optional. |
| Change pipeline | **Typed change specification** | No arbitrary HCL from API input. |
| Approval | **Boundary in workflow; GitHub Environment for optional real deploy** | One approval story; local simulation for DoD. |
| DNS / CIDR | **Fixtures required; live inventory optional** | Honest OPA limits. |
| Env AWS provision | **None required** | Config proves isolation; apply is optional. |
| Persistence | **SQLite + repository interface** | Local, free, swappable. |
| Terraform exec | **Adapter + fixtures + local backends** | Depth without cloud charges. |
| CI | **fmt/validate/lint/unit/policy/fixtures only** | Free Actions assumptions; no deploy. |
| Saved plan | **Hash verified pre-apply** | Core safety property. ADR-0002. |

---

## 3. Major Components and Responsibilities

### API service (`app/api`, `app/main.py`)

- Accept change requests for DNS, LB routes, TLS binding, SG rules.
- Authenticate demo callers; enforce idempotency keys on create.
- Expose request status, plan, policy, and verification views.
- Represent `awaiting_approval` as workflow state only.
- No Terraform orchestration in handlers.

### Domain layer (`app/domain`)

- Typed models, normalized **change specification**, lifecycle state machine.
- Network semantic validation that does not require AWS.
- No AWS SDK, Terraform, OPA, SQLite, FastAPI routes, or subprocess logic.

### Application services (`app/services`)

- Orchestrate validate → normalize → render → plan → policy → awaiting_approval
  → approval gate → hash verify → apply → verify.
- Idempotency and failure marking.

### Repositories (`app/repositories`)

- Persist requests, plan artifact metadata (**including hash**), policy,
  verification, audit — behind an interface (SQLite implementation).

### Terraform adapter (`app/infrastructure`)

- Consume **ChangeSpecification** only; render module inputs/composition.
- Controlled argv; saved plan + JSON + hash; apply only after hash verify.
- Default execution uses local/mock backends and fixtures.

### Policy layer (`policy/`)

- Conftest/OPA on plan JSON + inventory fixtures.
- ≥30 denied fixtures with blocker reporting.

### Verification (`app/verification`)

- DNS/TCP(/HTTPS) probes with retries.
- Required path: injectable resolvers / local compose endpoints.
- Optional path: real network endpoints (never required for DoD).

### Observability (`app/observability`)

- Structured logs; Prometheus-compatible `/metrics`.

### CI/CD (`.github/workflows`)

- PR: fmt, validate, lint, unit, policy, fixture plan eval.
- No AWS credentials, no apply, no billable cloud actions.
- Optional workflow docs may describe cloud apply; must not be required.

### Terraform (`terraform/`)

- Modules for network, SG, ALB, listener rule, DNS, TLS — **defined and
  statically validated**.
- Environment roots for dev/staging/prod with isolated state **design**.
- Bootstrap config for S3 + lockfile — validated as configuration; creating the
  bucket is optional.

### Local runtime (`docker-compose.yml`)

- Reproduce API + supporting behavior and failure modes as reasonably as
  possible without paid cloud dependencies.

---

## 4. Hardest Technical and Operational Risks

| Risk | Mitigation under zero-cost |
|---|---|
| Exact plan binding | Hash verify + tests; local apply of saved plans |
| Concurrent lock behavior | Simulate lock errors in adapter/failure tests |
| Policy vs live inventory | Required fixture inventory; document optional live path |
| DNS/TCP flakiness | Local doubles + bounded retry tests; optional real probes |
| Fake “deployed to AWS” claims | Evidence classes in §0; README discipline |
| Depth loss from avoiding AWS | Strong local integration, policy suite, IaC tests, failure injection |
| Accidental billable resources | Forbidden list in §0; CI has no AWS deploy job |

---

## 5. Spec Ambiguities — Resolutions

| Topic | Resolution |
|---|---|
| How requests become Terraform | Typed **change specification** → module inputs only. |
| Human approval | Workflow gate; GitHub Environment for optional real deploy. |
| Authentication | Bearer API keys for local demo. |
| Duplicate DNS / CIDR | Fixtures required; live reconciliation optional. |
| Three environments | Config + state design for all; **no AWS provision required**. |
| BUILD_SPEC “disposable AWS deployment” | Interpreted as **optional** under zero-cost hard constraint; DoD uses local + static IaC validation instead. |
| Persistence | SQLite behind repository interface. |
| LocalStack | Not default; only if it stays free/local and adds clear failure-fidelity value. |

### Explicit non-goals

- Required paid cloud usage of any kind
- Multi-cloud providers
- Multi-AZ / NAT “production” networking demos
- Service mesh / VPC lattice / PrivateLink productization
- General IAM / compute / database provisioning products
- Multi-tenant SaaS control plane
- Second independent API approval system
- PostgreSQL added for appearance
- Claiming AWS deployment without executing it

---

## 6. Final Repository Structure

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
├── .github/workflows/
├── app/
├── terraform/
│   ├── bootstrap/          # config only required; apply optional
│   ├── modules/
│   ├── environments/{dev,staging,prod}/
│   └── tests/
├── policy/
├── tests/{unit,integration,contract}/
├── scripts/
├── docs/
│   ├── architecture.md
│   ├── threat_model.md
│   ├── operations.md
│   ├── demo.md
│   ├── cost.md             # zero-cost required vs optional cloud
│   └── adr/
└── examples/requests/
```

---

## 7. Ordered Milestones and Acceptance Criteria

Each milestone ends with validation, then **stop** for the human-owned Git
handoff (§0a). Do not batch multiple milestones without approval.
Every milestone below is satisfiable at **$0**.
Agents never stage or commit; the owner commits after reviewing the handoff.

### Milestone 0 — Plan accepted

- [x] Plan reviewed; decisions locked (including zero-cost).

### Milestone 1 — Repository skeleton and ADRs

- [x] Layout, ADRs, `make help`.

### Milestone 2 — Domain models and validation

**Deliver**

- Domain types for four change kinds, environments, lifecycle states,
  normalized change specification, validation, state transitions.
- Comprehensive unit tests.

**Acceptance (zero-cost required)**

- [x] Invalid DNS/LB/TLS/SG inputs rejected with clear errors.
- [x] Lifecycle transitions enforced in domain tests (no handler logic yet).
- [x] Change specification is a distinct typed artifact (not raw HCL).

**Optional AWS validation:** none for this milestone.

### Milestone 3 — FastAPI change request API (persistence + status)

**Zero-cost required**

- [x] Create returns stable `request_id`; idempotent replay returns same request.
- [x] Handlers contain no Terraform subprocess / HCL construction from user strings.
- [x] Auth, validation, create/get covered by local tests.
- [x] Runnable via local process and/or Docker Compose.

**Optional AWS validation:** none.

### Milestone 4 — Terraform module foundation (network + shared patterns)

**Zero-cost required**

- [x] `terraform fmt -check` and `terraform validate` succeed (local backend).
- [x] No environment-specific constants in modules.
- [x] Module tests / validation blocks where practical.
- [x] No NAT Gateway resources in required examples.

**Optional AWS validation:** `terraform plan` against a real account (never required).

### Milestone 5 — Security group + DNS modules

**Zero-cost required**

- [x] Module validation rejects unsafe defaults where expressible.
- [x] Renderer maps change specs → deterministic Terraform inputs.
- [x] Configuration tests without applying cloud resources.

**Optional AWS validation:** live plan only.

### Milestone 6 — ALB + listener rule + TLS modules

**Zero-cost required**

- [ ] All four request types render to Terraform inputs.
- [ ] Modules expose outputs needed for cross-stack refs / verification contracts.
- [ ] Modules are `fmt`/`validate`/test clean; **no required apply** of ALB/NLB.

**Optional AWS validation:** live plan/apply explicitly opted into by the operator.

### Milestone 7 — Terraform command adapter + plan artifacts

**Zero-cost required**

- [ ] Plan → saved binary/JSON + hash (local terraform or injected runner).
- [ ] Apply refuses missing plan; mismatched hash rejected.
- [ ] No user-controlled arbitrary Terraform flags.
- [ ] Integration tests cover hash binding without AWS.

**Optional AWS validation:** none required.

### Milestone 8 — Remote state design and environment isolation

**Zero-cost required**

- [ ] Three environment roots with distinct backend configuration/state keys.
- [ ] ADR/docs explain workspaces rejection and S3 lockfile design.
- [ ] Cross-stack dependency wiring via outputs (config-level).
- [ ] Local backend path works for demo applies.
- [ ] Bootstrap module/config exists and is statically validated — **creating a
      real S3 bucket is optional**.

**Optional AWS validation:** bootstrap + remote state in a real account.

### Milestone 9 — OPA/Conftest policy engine

**Zero-cost required**

- [ ] `conftest test` runs locally without AWS.
- [ ] Allowed + denied fixtures per rule; clear blocker messages.
- [ ] Inventory fixtures for DNS/CIDR cases; limits documented.

**Optional AWS validation:** evaluate a live-produced plan JSON offline.

### Milestone 10 — ≥30 negative policy fixtures

**Zero-cost required**

- [ ] ≥30 denied cases fail for the expected policy in CI/local.
- [ ] Deterministic suite; no hardcoded “pass” docs standing in for output.

**Optional AWS validation:** none.

### Milestone 11 — GitHub Actions PR pipeline

**Zero-cost required**

- [ ] PR workflow: fmt, validate, lint, unit, policy, fixture plan evaluation.
- [ ] No AWS credentials; no apply; no billable cloud actions.
- [ ] Stays within free GitHub Actions assumptions for a typical private/public repo.

**Optional AWS validation:** none in PR CI.

### Milestone 12 — Approval boundary + saved-plan apply path

**Zero-cost required**

- [ ] Local/CI path demonstrates approval gate → hash verify → apply **exact**
      saved plan (local/mock backend).
- [ ] Tampered/mismatched hash rejected.
- [ ] Apply path does not silently regenerate a plan.
- [ ] Workflow YAML documents how GitHub Environment would gate an optional
      real deploy — without requiring that deploy.

**Optional AWS validation:** GitHub Environment-protected apply to a real account.

### Milestone 13 — DNS and TCP verification

**Zero-cost required**

- [ ] Probes with timeout/backoff; injectable dependencies.
- [ ] Local integration against Compose or test doubles.
- [ ] Verification failure marks request unhealthy/failed.

**Optional AWS validation:** probes against real endpoints after optional apply.

### Milestone 14 — Observability and audit history

**Zero-cost required**

- [ ] Required log fields; `/metrics`; no credential leakage; local tests.

**Optional AWS validation:** none.

### Milestone 15 — Failure injection tests

**Zero-cost required**

- [ ] Lock, plan failure, policy unavailable/rejection, apply failure, DNS delay,
      TCP verify failure, partial dependency failure, duplicate request, retry.
- [ ] Retries do not duplicate intent for identical idempotency keys.

**Optional AWS validation:** none.

### Milestone 16 — End-to-end control-plane validation (required local) + optional AWS

**Zero-cost required**

- [ ] Full workflow exercised locally: request → validate → change spec → plan
      fixture or local plan → policy → approval gate → hash verify → apply
      (local backend) → verification doubles → audit.
- [ ] Evidence captured from the actual local/CI run.
- [ ] README/demo distinguish evidence classes (§0).
- [ ] No billable AWS resources created by the required path.

**Optional AWS validation**

- [ ] Operator-run sandbox apply in their own account, if they choose.
- [ ] Only document results if actually executed.
- [ ] Must still avoid leaving billable resources running; destroy immediately.
- [ ] Not required for Definition of Done.

### Milestone 17 — Documentation and demo polish

**Zero-cost required**

- [ ] README with Mermaid, capabilities, policy rejection evidence from CI/local,
      limitations, **zero-cost notes**, evidence-class labeling.
- [ ] Architecture, threat model, operations, demo runnable without AWS.
- [ ] No fabricated benchmarks; no false AWS deployment claims.

**Optional AWS validation:** appendix optional cloud results only if real.

---

## 8. Local vs optional cloud

| Milestone | Required path | Optional cloud |
|---|---|---|
| 0–3 | Local only | — |
| 4–6 | fmt/validate/tflint/tests | live `plan`/`apply` |
| 7 | Local adapter + fixtures | — |
| 8 | Config + local backend | real S3 bootstrap |
| 9–11 | Local + free CI | offline eval of a live plan JSON |
| 12–15 | Local/Compose/CI | real deploy/probes |
| 16 | **Local E2E required** | AWS E2E optional |
| 17 | Docs from required evidence | optional cloud appendix |

---

## 9. Cost policy (locked)

### Required

- Spend **$0**.
- Validate with local tooling, Docker Compose, fixtures, and free CI.
- Keep AWS-shaped Terraform in-repo and statically validated.

### Optional cloud (operator-owned)

If someone opts into AWS despite DoD not requiring it:

- They accept any charges.
- Do not create the forbidden required-workflow resources as part of **project CI**.
- Document results only when actually run.
- Destroy promptly; never leave ALBs/zones/etc. running “for the portfolio.”

### Claim hygiene

| OK | Not OK |
|---|---|
| “Terraform modules for ALB/DNS/SG validated with fmt/validate/policy fixtures” | “Deployed ALB to AWS” (unless true) |
| “Saved plan hash binding verified in local integration tests” | “Production AWS apply pipeline exercised” (unless true) |
| “DNS/TCP verification implemented and tested with local doubles” | “Verified against Route 53 / live ALB” (unless true) |

---

## 10. Mapping resume claims → evidence (zero-cost)

| Claim | Required evidence |
|---|---|
| FastAPI for DNS/LB/TLS/SG requests | API + local tests + examples |
| Versioned Terraform modules with validation | Modules + fmt/validate/tests in CI |
| Isolated envs + remote state **design** | `environments/*` + bootstrap config + ADR-0001 |
| Cross-stack via outputs | Config wiring + docs |
| CI fmt/validate/lint/policy + fixture plan eval | `pull_request.yml` logs |
| Unsafe changes rejected | ≥30 denied fixtures + CI output |
| Only reviewed saved plan applied | Hash verify tests + local apply path |
| Post-apply DNS/TCP verification | Local verification tests (+ optional cloud if run) |
| ≥30 unsafe suite | `policy/tests/denied` |

---

## 11. Suggested commit cadence (owner-executed)

These are **suggestions for the human owner**. Agents propose messages and
commands; only the owner runs `git add` / `git commit` / `git push`.

1. `docs: add build plan and repository skeleton with ADRs`
2. `feat(domain): add change models, validation, and lifecycle transitions`
3. `feat(api): add change request API with idempotency and persistence`
4. `feat(terraform): add network module and environment skeletons`
5. `feat(terraform): add security group and DNS modules`
6. `feat(terraform): add ALB, listener rule, and TLS modules`
7. `feat(infra): add Terraform plan/apply adapter with plan identity`
8. `feat(terraform): add state backend design and env isolation`
9. `feat(policy): add OPA/Conftest policies for plan JSON`
10. `test(policy): add thirty-plus denied infrastructure fixtures`
11. `ci: add pull request fmt validate lint test and policy workflow`
12. `feat(deploy): bind approval gate to exact saved plan apply`
13. `feat(verify): add DNS and TCP verification with local doubles`
14. `feat(obs): add structured audit logs and metrics`
15. `test: add failure injection coverage for control plane paths`
16. `test: add local end-to-end control-plane validation evidence`
17. `docs: polish README with zero-cost evidence classes`

Zero-cost plan updates and the git-ownership rule may land as separate
owner commits (for example `docs: lock zero-cost DoD` and
`docs: record human-only git ownership rule`) when those changes are ready.

---

## 12. Stop discipline

After each milestone:

1. Validate acceptance criteria ($0 path).
2. Perform the §0a Git handoff (results, diff summary, file list, suggested
   commits/commands).
3. **Stop.** Do not stage or commit.
4. Wait for the owner to confirm commits before the next milestone.

Do not batch multiple milestones without approval.
Never treat “proceed” / “continue” / “finish” as commit permission.
