# NextDNS Optimized Analytics — Makefile
# Unified CLI task runner 🧱
#
# Usage: make <target>
# Run `make help` to see all available targets.

SHELL := /bin/bash
.DEFAULT_GOAL := help

# Directories
BACKEND_DIR  := backend
FRONTEND_DIR := frontend

# Backend virtualenv activation (relative — always used after cd into BACKEND_DIR)
ACTIVATE := source venv/bin/activate

# ==================== Help ====================

.PHONY: help
help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-24s\033[0m %s\n", $$1, $$2}' | \
		sort

# ==================== Setup ====================

.PHONY: install setup-backend setup-frontend
install: setup-backend setup-frontend ## Install all dependencies (backend + frontend)

setup-backend: ## Set up backend virtualenv and install dependencies
	cd $(BACKEND_DIR) && python3 -m venv venv && \
		$(ACTIVATE) && pip install --upgrade pip && \
		pip install -r requirements.txt && \
		pip install -r requirements-dev.txt

setup-frontend: ## Install frontend npm dependencies
	cd $(FRONTEND_DIR) && npm install

# ==================== Development ====================

.PHONY: dev dev-frontend dev-backend
dev-frontend: ## Start frontend dev server (Vite)
	cd $(FRONTEND_DIR) && npm run dev

dev-backend: ## Start backend dev server (uvicorn)
	cd $(BACKEND_DIR) && $(ACTIVATE) && uvicorn main:app --reload --port 5001

# ==================== Testing ====================

.PHONY: test test-frontend test-backend test-coverage
test: test-backend test-frontend ## Run all tests (backend + frontend)

test-backend: ## Run backend tests (pytest)
	cd $(BACKEND_DIR) && $(ACTIVATE) && pytest tests/ -v

test-frontend: ## Run frontend tests (vitest)
	cd $(FRONTEND_DIR) && npm run test -- --run

test-coverage: ## Run all tests with coverage reports
	cd $(BACKEND_DIR) && $(ACTIVATE) && pytest tests/ --cov=. --cov-report=html --cov-report=term
	cd $(FRONTEND_DIR) && npm run test:coverage

# ==================== Linting & Formatting ====================

.PHONY: lint lint-frontend lint-backend lint-workflows format format-check
lint: lint-backend lint-frontend ## Run all linters

lint-backend: ## Lint backend (Black check + Pylint)
	cd $(BACKEND_DIR) && $(ACTIVATE) && \
		black . --check --line-length=88 --extend-exclude='(alembic|venv)' && \
		pylint . --rcfile=../.pylintrc

lint-frontend: ## Lint frontend (ESLint + TypeScript + Prettier)
	cd $(FRONTEND_DIR) && npm run lint && npm run type-check && npm run format:check

lint-workflows: ## Lint GitHub Actions workflows (actionlint)
	actionlint .github/workflows/*.yml

format: ## Auto-format all code (Black + Prettier)
	cd $(BACKEND_DIR) && $(ACTIVATE) && black . --line-length=88 --extend-exclude='(alembic|venv)'
	cd $(FRONTEND_DIR) && npm run format

format-check: ## Check formatting without modifying files
	cd $(BACKEND_DIR) && $(ACTIVATE) && black . --check --line-length=88 --extend-exclude='(alembic|venv)'
	cd $(FRONTEND_DIR) && npm run format:check

# ==================== Security ====================

.PHONY: security security-backend security-frontend
security: security-backend security-frontend ## Run all security scans

security-backend: ## Run backend security scan (Bandit)
	cd $(BACKEND_DIR) && $(ACTIVATE) && bandit -r . -x ./tests/ -x ./venv/ --skip B101

security-frontend: ## Run frontend security audit (npm audit)
	cd $(FRONTEND_DIR) && npm audit --audit-level=moderate

# ==================== Docker ====================

.PHONY: build up down logs health
build: ## Build and start Docker containers
	docker-compose up -d --build

up: ## Start Docker containers (no rebuild)
	docker-compose up -d

down: ## Stop Docker containers
	docker-compose down

logs: ## Tail Docker container logs
	docker-compose logs -f

health: ## Check service health endpoints
	@echo "🏥 Backend health..."
	@curl -sf http://localhost:5001/health | python3 -m json.tool || echo "❌ Backend not responding"
	@echo ""
	@echo "🏥 Frontend health..."
	@curl -sfI http://localhost:5002/ | head -1 || echo "❌ Frontend not responding"

# ==================== Database ====================

.PHONY: db-init db-clear db-migrate
db-init: ## Initialise the database (create tables)
	cd $(BACKEND_DIR) && $(ACTIVATE) && python manage_db.py init

db-clear: ## Clear all data from the database
	cd $(BACKEND_DIR) && $(ACTIVATE) && python manage_db.py clear

db-migrate: ## Run Alembic database migrations
	cd $(BACKEND_DIR) && $(ACTIVATE) && python manage_db.py upgrade

# ==================== Quality Gates ====================

.PHONY: check check-frontend check-backend pre-push
check: check-backend check-frontend ## Run full quality check (lint + test + security)

check-backend: lint-backend test-backend security-backend ## Full backend quality check

check-frontend: lint-frontend test-frontend security-frontend ## Full frontend quality check

pre-push: check lint-workflows build health ## Pre-push gate (all checks + Docker build + health)
	@echo ""
	@echo "✅ All quality gates passed — ready to push!"
