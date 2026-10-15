# Switchyard

## Build Specification for Cursor

### Mission

Build Switchyard as a production style network infrastructure control
plane for internal application teams.

The product should let an application engineer request a small set of
approved network capabilities through an API without editing Terraform
directly. The system translates validated requests into versioned
infrastructure changes, evaluates policy before deployment, requires an
explicit review boundary, applies only the reviewed plan, and verifies
the resulting network behavior.

The repository should demonstrate that network automation is not merely
script execution. It should show careful API design, infrastructure
state management, policy enforcement, failure handling, observability,
testing, and operational safety.

The final repository must be understandable to a senior platform or
network engineer within five minutes and deep enough to sustain a
technical interview.

### Resume Claims This Repository Must Prove

The finished implementation must provide reproducible evidence for these
claims.

1.  A FastAPI service allows application teams to request DNS records,
    load balancer routes, TLS configuration, and security group rules.

2.  Infrastructure is composed from reusable and versioned Terraform
    modules with validated inputs.

3.  Development, staging, and production environments are isolated and
    use remote Terraform state.

4.  Cross stack dependencies are passed through explicit outputs rather
    than manually copied values.

5.  CI runs Terraform formatting, validation, linting, and policy checks
    before infrastructure changes can proceed.

6.  Unsafe changes are rejected by automated policy.

7.  Only a reviewed saved plan may be applied.

8.  Successful applies are followed by DNS and TCP verification.

9.  The repository contains a reproducible suite of at least thirty
    intentionally unsafe infrastructure changes and demonstrates that
    the expected policies reject them.

Do not hardcode successful results into documentation. Tests and CI
artifacts must produce the evidence.

## Product Boundary

Switchyard is intentionally narrow.

It is not a general cloud management platform.

It supports four initial request types.

1.  DNS record creation and modification

2.  Load balancer listener and route configuration

3.  TLS certificate attachment or reference

4.  Security group rule changes

The API should expose these concepts as safe product abstractions rather
than accepting arbitrary Terraform.

A caller should not be able to submit raw HCL through the API.

## Architecture

The system should separate request handling, domain validation,
infrastructure rendering, policy evaluation, execution, and
verification.

### Control Flow

Application request

FastAPI

Pydantic request model

Domain validation

Infrastructure change specification

Terraform module composition

Terraform plan

Plan JSON

OPA policy evaluation

Human approval boundary

Saved plan apply

Post apply DNS and TCP verification

Audit record

### Core Components

#### API Service

Use Python and FastAPI.

Responsibilities:

Accept network change requests

Validate request shape

Authenticate callers in the local demonstration environment

Generate a stable request identifier

Persist request status

Invoke the infrastructure workflow through a clean service interface

Expose request history and execution status

Never execute arbitrary shell text supplied by the user

#### Domain Layer

Create explicit domain models for:

DNS record

Load balancer route

TLS binding

Security group rule

Environment

Change request

Plan result

Policy result

Verification result

Keep cloud provider details outside the domain layer where practical.

#### Terraform Layer

Create reusable modules for:

VPC and subnet foundation

Security groups

Application Load Balancer

Listener rules

Route 53 records

TLS related configuration

Each module must have:

Typed variables

Validation blocks

Outputs

Useful descriptions

No embedded environment specific constants

Examples

Tests where practical

Pin provider and module versions.

#### State Model

Use an S3 backend for the AWS validation environment.

Use the current supported S3 state locking mechanism when implemented.

Do not copy an outdated state locking pattern simply because an older
resume draft mentioned it.

Create explicit environment separation for development, staging, and
production.

Document the tradeoff between Terraform workspaces and separate state
roots. Choose one deliberately and explain the decision in an
Architecture Decision Record.

Cross stack dependencies must use explicit outputs and controlled state
references.

#### Policy Layer

Use OPA with Conftest against Terraform plan JSON.

Policies should include at minimum:

Reject unrestricted administrative ingress

Reject dangerous public ingress patterns

Reject invalid or overlapping CIDR ranges where the project can
determine them

Reject duplicate DNS ownership

Reject unsupported listener ports

Reject insecure listener configuration

Reject deletion of protected resources

Reject resources missing required ownership metadata

Reject wildcard rules outside explicitly approved cases

Reject environment boundary violations

Reject unexpected resource types

Create at least thirty seeded negative cases distributed across these
categories.

The test suite should report exactly which policy blocked each case.

#### CI Pipeline

Use GitHub Actions.

Pull request workflow:

Terraform format check

Terraform validate

tflint

Unit tests

Policy tests

Terraform plan

Terraform show JSON

Conftest evaluation

Upload plan artifact

Publish concise plan summary

No automatic apply from an unreviewed pull request

Deployment workflow:

Require protected environment approval

Download the exact saved plan artifact

Verify artifact identity

Apply that saved plan

Run post apply verification

Persist deployment result

The apply stage must not silently generate a new plan.

### Verification Layer

After an apply, verify behavior rather than assuming Terraform success
means the network works.

Implement:

DNS resolution probe

TCP connection probe

Optional HTTPS probe

Expected certificate inspection where applicable

Expected status code check

Timeout behavior

Retry with bounded backoff

Verification failures must mark the deployment unhealthy and produce
actionable output.

## API Design

Suggested endpoints:

`POST /v1/changes`

`GET /v1/changes/{request_id}`

`GET /v1/changes/{request_id}/plan`

`GET /v1/changes/{request_id}/policy`

`GET /v1/changes/{request_id}/verification`

`GET /health`

Use idempotency keys for create operations.

Define clear lifecycle states such as:

requested

validated

planned

policy_rejected

awaiting_approval

applying

verifying

succeeded

failed

Do not let HTTP handlers contain Terraform orchestration logic directly.

## Suggested Repository Structure

``` text
switchyard/
  README.md
  LICENSE
  Makefile
  pyproject.toml
  docker-compose.yml
  .env.example
  .gitignore
  .github/
    workflows/
      pull_request.yml
      deploy.yml
  app/
    api/
    domain/
    services/
    repositories/
    infrastructure/
    verification/
    observability/
    main.py
  terraform/
    modules/
      network/
      security_group/
      alb/
      listener_rule/
      dns/
      tls/
    environments/
      dev/
      staging/
      prod/
    tests/
  policy/
    terraform/
    tests/
      allowed/
      denied/
  tests/
    unit/
    integration/
    contract/
  scripts/
    seed_policy_cases.py
    verify_dns.py
    verify_tcp.py
  docs/
    architecture.md
    threat_model.md
    operations.md
    demo.md
    adr/
  examples/
    requests/
```

## Testing Strategy

### Python Tests

Test:

Request validation

Idempotency

State transitions

Domain validation

Terraform command adapter behavior

Policy result parsing

Verification retries

Failure propagation

Audit history

Use dependency injection around external commands and AWS integrations.

### Terraform Tests

Test module input validation and important resource properties.

Where provider access is unnecessary, keep tests local.

Where AWS is required, use a dedicated disposable environment.

### Policy Tests

Every OPA rule needs:

At least one allowed fixture

At least one denied fixture

A descriptive failure reason

A stable test name

The seeded unsafe change suite must contain at least thirty cases.

### Integration Tests

Run a complete local workflow using fixtures:

API request

Generated change specification

Terraform plan fixture

OPA evaluation

Approval simulation

Verification simulation

Audit result

### Failure Tests

Explicitly test:

State already locked

Terraform plan failure

Policy engine unavailable

Policy rejection

Apply failure

DNS propagation delay

TCP verification failure

Partial external dependency failure

Duplicate request

Retry after failure

## Security Requirements

No secrets in Git.

Use `.env.example` only for names and placeholders.

Use least privilege IAM for the AWS demonstration.

Separate plan permissions from apply permissions where practical.

Never allow arbitrary Terraform arguments from API input.

Validate all network inputs.

Log actor, request, policy decision, plan identity, apply result, and
verification result.

Avoid logging credentials, tokens, or private key material.

Create `docs/threat_model.md` describing trust boundaries and abuse
cases.

## Observability

Emit structured logs with:

request_id

environment

actor

change_type

state

duration_ms

policy_result

terraform_exit_code

verification_result

Expose Prometheus compatible application metrics if practical.

At minimum include:

change requests total

policy rejections total

apply failures total

verification failures total

workflow duration

request state counts

## Local Development

The default developer experience should not require paid AWS
infrastructure.

Provide a single documented command that starts the API and supporting
local services.

Use fixtures and mocks for Terraform execution during normal
development.

Real AWS deployment should be an explicit validation path, not a
requirement for every test run.

## AWS Cost Discipline

Do not leave billable resources running.

Use a dedicated sandbox account or isolated environment if available.

Tag every resource with project and owner metadata.

Provide a destroy command.

Document which resources can incur charges.

Avoid NAT Gateway unless it is genuinely required.

Provision real infrastructure only long enough to validate the workflow.

## Git History Plan

Do not build the repository as one giant commit.

Suggested progression:

1.  Repository skeleton and architecture decision record

2.  Domain models and request validation

3.  FastAPI change request API

4.  Terraform module foundation

5.  DNS workflow

6.  Load balancer workflow

7.  Security group workflow

8.  TLS workflow

9.  Remote state and environment isolation

10. OPA policy engine

11. Negative policy fixtures

12. GitHub Actions plan pipeline

13. Approval and saved plan apply path

14. DNS and TCP verification

15. Observability and audit history

16. Failure injection tests

17. AWS end to end validation

18. Documentation and demo polish

Each commit should leave the repository in a coherent state.

## Public README Requirements

The public README is separate from this build specification.

It should include:

A concise problem statement

A simple architecture diagram

A short demonstration flow

A table of supported network capabilities

A policy enforcement example

A screenshot or captured CI artifact showing a rejected unsafe change

A successful request example

A verification example

Local setup

Optional AWS deployment instructions

Testing commands

Design tradeoffs

Known limitations

Cost notes

Do not write the README like a tutorial assignment.

Do not mention that the project was built for a job application.

## Architecture Diagram

Create the final diagram using Mermaid in the public README.

It should communicate:

Application engineer

Switchyard API

Validation

Terraform plan

OPA policy gate

Approval

Terraform apply

AWS network resources

DNS and TCP verification

Audit and observability

Keep the diagram readable.

## Senior Engineer Review Bar

A senior engineer reviewing this repository should be able to answer yes
to the following:

Is the API boundary safer than giving users raw Terraform access?

Are infrastructure changes deterministic and reviewable?

Can an unsafe plan be rejected before apply?

Can the exact reviewed plan be proven to be the one applied?

Are failures visible and actionable?

Can the system recover from retries without creating duplicate intent?

Are module boundaries sensible?

Is state ownership explicit?

Are environment boundaries clear?

Can the author explain why every major component exists?

Can the claims in the README be reproduced?

## Interview Defense

Be prepared to explain:

Why use a control plane instead of direct Terraform access

Why FastAPI is appropriate here

How idempotency works

How concurrent change requests are handled

How Terraform state locking works

Why plan JSON is evaluated instead of raw HCL

What OPA adds beyond Terraform validation

How an approved plan is bound to the eventual apply

How cross stack dependencies are handled

How rollback differs for DNS, listener, and security group changes

What happens if apply succeeds but verification fails

How DNS propagation affects verification

How least privilege applies to the deployment workflow

How you would support multiple cloud providers later

How you would design ownership and tenancy at larger scale

## Definition of Done

Switchyard is complete only when:

The API accepts all supported change types

Terraform modules exist and are tested

Environment state separation is implemented

Policy checks execute against plan JSON

At least thirty unsafe fixtures are automatically rejected

A reviewed saved plan can be applied

Post apply DNS and TCP verification works

Failure paths are tested

CI runs automatically

A disposable AWS deployment has been validated

All infrastructure can be destroyed cleanly

The README contains reproducible evidence

No resume metric is based on a hardcoded or invented result

## Cursor Working Rules

Implement in small coherent phases.

Do not skip tests to move faster.

Do not fabricate benchmark or policy results.

Do not place business logic directly in API route handlers.

Do not make AWS mandatory for ordinary development.

Do not commit secrets.

Do not silently replace a difficult requirement with a mock and call the
project complete.

Mocks are appropriate for unit tests. Final acceptance requires the
relevant real integration path.

After every phase:

Run formatting

Run linting

Run tests

Update documentation

Make one coherent commit

Before declaring the project complete, run the entire acceptance suite
from a clean checkout.
