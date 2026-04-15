.PHONY: help dev backend frontend install install-backend install-frontend test lint db-migrate

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# === Setup ===
install: install-backend install-frontend ## Install all dependencies

install-backend: ## Install Python backend dependencies
	cd backend && uv sync

install-frontend: ## Install Next.js frontend dependencies
	cd frontend && pnpm install

# === Development ===
dev: ## Run both backend and frontend dev servers
	@echo "Starting backend on :8000 and frontend on :3000..."
	@make backend & make frontend & wait

backend: ## Run FastAPI backend dev server
	cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend: ## Run Next.js frontend dev server
	cd frontend && pnpm dev

# === Testing ===
test: ## Run all backend tests
	cd backend && uv run pytest -v

test-cov: ## Run tests with coverage
	cd backend && uv run pytest --cov=app --cov-report=html -v

# === Linting ===
lint: ## Lint backend code
	cd backend && uv run ruff check .

lint-fix: ## Auto-fix lint issues
	cd backend && uv run ruff check --fix .

# === Database ===
db-migrate: ## Run database migrations
	cd backend && uv run alembic upgrade head

db-revision: ## Create new migration (usage: make db-revision msg="add xyz")
	cd backend && uv run alembic revision --autogenerate -m "$(msg)"
