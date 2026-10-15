# Switchyard — common developer targets
# Milestone 1: stubs only. Later milestones wire real commands.

.DEFAULT_GOAL := help

.PHONY: help install fmt lint test test-unit test-policy validate-tf \
	plan-fixtures up down destroy-sandbox clean

help: ## Show available targets
	@awk 'BEGIN {FS = ":.*##"; printf "Switchyard targets:\n\n"} \
		/^[a-zA-Z0-9_-]+:.*?##/ { printf "  %-20s %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

install: ## Install Python package and dev dependencies
	@echo "TODO(M2+): install via pyproject.toml (uv/pip)"
	@echo "  Example: pip install -e \".[dev]\""

fmt: ## Format Python and Terraform sources
	@echo "TODO(M2+): ruff format / terraform fmt"

lint: ## Lint Python and Terraform sources
	@echo "TODO(M2+): ruff check / tflint"

test: ## Run the default local test suite
	@echo "TODO(M2+): pytest"
	@$(MAKE) test-unit
	@$(MAKE) test-policy

test-unit: ## Run Python unit tests
	@echo "TODO(M2+): pytest tests/unit"

test-policy: ## Run OPA/Conftest policy tests (fixture-based)
	@echo "TODO(M9+): conftest test policy/tests"

validate-tf: ## Terraform fmt-check and validate (local, no AWS apply)
	@echo "TODO(M4+): terraform fmt -check / terraform validate"

plan-fixtures: ## Evaluate fixture plan JSON with policy (no AWS)
	@echo "TODO(M9+): fixture-based plan evaluation for CI"

up: ## Start local API and supporting services
	@echo "TODO(M3+): docker compose up --build"

down: ## Stop local services
	@echo "TODO(M3+): docker compose down"

destroy-sandbox: ## Optional: destroy operator-owned AWS resources (never required for DoD)
	@echo "TODO(M16 optional): scripts/destroy_sandbox.sh"
	@echo "Definition of Done is \$0 — AWS destroy is only for optional cloud runs."

clean: ## Remove local caches and generated artifacts
	@rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov artifacts
	@find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
