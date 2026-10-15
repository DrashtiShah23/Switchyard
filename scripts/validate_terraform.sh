#!/usr/bin/env bash
# Zero-cost Terraform static validation for Milestone 4+.
# Does not call real AWS APIs for apply and does not create billable resources.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if ! command -v terraform >/dev/null 2>&1; then
  echo "terraform is required on PATH for validate_terraform.sh" >&2
  exit 1
fi

echo "==> terraform fmt -check"
terraform fmt -check -recursive terraform

validate_root() {
  local dir="$1"
  echo "==> terraform init/validate: ${dir}"
  (
    cd "${dir}"
    terraform init -backend=false -input=false >/dev/null
    terraform validate
  )
}

validate_root "terraform/modules/network/examples/public_two_az"
validate_root "terraform/environments/dev"
validate_root "terraform/environments/staging"
validate_root "terraform/environments/prod"

echo "==> terraform test (network variable validations)"
(
  cd "terraform/modules/network"
  terraform init -backend=false -input=false >/dev/null
  terraform test
)

echo "==> OK: terraform static validation passed"
