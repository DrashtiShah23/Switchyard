# Switchyard — common developer targets

.DEFAULT_GOAL := help

.PHONY: help install fmt lint typecheck test test-unit test-policy validate-tf \
	plan-fixtures up down destroy-sandbox clean

help: ## Show available targets
	@awk 'BEGIN {FS = ":.*##"; printf "Switchyard targets:\n\n"} \
		/^[a-zA-Z0-9_-]+:.*?##/ { printf "  %-20s %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

install: ## Install Python package and dev dependencies
	pip install -e ".[dev]"

fmt: ## Format Python sources
	ruff format app tests

lint: ## Lint Python sources
	ruff check app tests

typecheck: ## Run mypy on the application package
	mypy app

test: ## Run the default local test suite
	pytest -q

test-unit: ## Run Python unit/API tests
	pytest -q tests/unit tests/contract

test-policy: ## Run OPA/Conftest policy tests (fixture-based)
	@echo "TODO(M9+): conftest test policy/tests"

validate-tf: ## Terraform fmt-check and validate (local, no AWS apply)
	@echo "TODO(M4+): terraform fmt -check / terraform validate"

plan-fixtures: ## Evaluate fixture plan JSON with policy (no AWS)
	@echo "TODO(M9+): fixture-based plan evaluation for CI"

up: ## Start local API via Docker Compose
	mkdir -p data
	docker compose up --build -d

down: ## Stop local Docker Compose services
	docker compose down

destroy-sandbox: ## Optional: destroy operator-owned AWS resources (never required for DoD)
	@echo "TODO(M16 optional): scripts/destroy_sandbox.sh"
	@echo "Definition of Done is \$0 — AWS destroy is only for optional cloud runs."

clean: ## Remove local caches and generated artifacts
	@rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov artifacts
	@find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
