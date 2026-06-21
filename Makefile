.PHONY: help dev down logs seed test lint hooks lint-backend

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

test: ## Run backend + frontend tests
	docker compose exec backend pytest
	cd frontend && npm test

lint: ## Run linters
	docker compose exec backend ruff check .
	cd frontend && npm run lint

hooks: ## Install pre-commit git hooks (ruff check on commit)
	uv run --project backend pre-commit install

lint-backend: ## Run backend ruff locally (no docker)
	cd backend && uv run ruff check .
