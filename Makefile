.PHONY: help dev down logs seed test lint hooks lint-backend lint-backend-fix verify-e2e verify-dlq

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

dev: ## Start all services via Docker Compose
	docker compose up --build

down: ## Stop all services
	docker compose down

logs: ## Tail all service logs
	docker compose logs -f

seed: ## Seed local database with sample data
	./scripts/seed.sh

verify-e2e: ## Run full pipeline E2E smoke test (requires all workers running)
	./scripts/verify-pipeline-e2e.sh

verify-dlq: ## Verify SQS redrive policies on worker queues (requires LocalStack)
	./scripts/verify-dlq-redrive.sh

test: ## Run backend + frontend tests
	docker compose exec backend pytest
	cd frontend && npm test

lint: ## Run linters
	docker compose exec backend ruff check .
	cd frontend && npm run lint

hooks: ## Install pre-commit git hooks (ruff check on commit)
	uv run --project backend pre-commit install

lint-backend: ## Run backend ruff locally (no docker)
	uv run --project backend ruff check --config backend/pyproject.toml backend/

lint-backend-fix: ## Auto-fix backend ruff issues (matches pre-commit)
	uv run --project backend ruff check --fix --config backend/pyproject.toml backend/
