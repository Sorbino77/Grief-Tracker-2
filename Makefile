# ShipTrack — comprehensive development tasks
# Run `make` (or `make help`) to see all available targets
.DEFAULT_GOAL := help

.PHONY: help up down sync migrate seed test coverage lint format fix check \
        clean clean-cache clean-pycache clean-all docker-up docker-down docker-logs \
        shell migrations show-migrations watch-tests security type-check format-check \
        install-dev install-prod collect-static reset-db fresh-db admin-user \
        import-demo backup-db shell-db create-superuser

# ============================================================================
# HELP & DOCUMENTATION
# ============================================================================

help:  ## 📋 Show this help message
	@echo "ShipTrack — Development Tasks"
	@echo "=================================================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	  | awk 'BEGIN{FS=":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}' \
	  | sort

# ============================================================================
# SETUP & DEPENDENCIES
# ============================================================================

install-dev:  ## 📦 Install all dependencies (dev + main)
	@echo "Installing development dependencies..."
	@uv sync

install-prod:  ## 📦 Install production dependencies only
	@echo "Installing production dependencies..."
	@uv sync --no-dev

sync:  ## 🔄 Sync/refresh all dependencies
	@echo "Syncing dependencies..."
	@uv sync

# ============================================================================
# SERVER & DEVELOPMENT
# ============================================================================

up:  ## 🚀 Start dev server (auto-opens browser)
	@bash scripts/launch.sh

down:  ## 🛑 Stop dev server
	@echo "Stopping dev server..."

shell:  ## 🐚 Open Django interactive shell
	@uv run python manage.py shell

shell-db:  ## 🐚 Open Django database shell
	@uv run python manage.py dbshell

# ============================================================================
# DATABASE OPERATIONS
# ============================================================================

migrate:  ## 🗄️  Apply all pending migrations
	@echo "Applying migrations..."
	@uv run python manage.py migrate

migrations:  ## 📝 Show migration status
	@uv run python manage.py showmigrations

show-migrations:  ## 📊 Display all migrations (detailed)
	@uv run python manage.py showmigrations --list

makemigrations:  ## ✏️  Create migrations for model changes
	@uv run python manage.py makemigrations

reset-db:  ## ⚠️  Reset database (DELETE ALL DATA)
	@echo "⚠️  WARNING: This will DELETE ALL data in the database!"
	@read -p "Are you sure? Type 'yes' to confirm: " confirm && \
	[ "$$confirm" = "yes" ] && \
	(rm -f db.sqlite3 && echo "✓ Database file removed") || echo "Cancelled"

fresh-db: reset-db migrate seed  ## 🆕 Reset, migrate, and seed database
	@echo "✓ Fresh database ready!"

backup-db:  ## 💾 Backup database (SQLite only)
	@cp db.sqlite3 db.sqlite3.backup.$(shell date +%Y%m%d_%H%M%S)
	@echo "✓ Database backed up"

# ============================================================================
# USER MANAGEMENT
# ============================================================================

seed:  ## 🌱 Seed demo data (carriers, locations, etc.)
	@uv run python manage.py seed_demo

admin-user:  ## 👤 Create superuser (interactive)
	@uv run python manage.py createsuperuser

create-superuser:  ## 👤 Create superuser (non-interactive)
	@echo "Creating superuser..."
	@uv run python manage.py shell -c \
		"from django.contrib.auth import get_user_model; \
		User = get_user_model(); \
		User.objects.filter(username='admin').delete(); \
		User.objects.create_superuser('admin', 'admin@example.com', 'admin123')" && \
	echo "✓ Superuser 'admin' created (password: admin123)"

# ============================================================================
# TESTING
# ============================================================================

test:  ## ✅ Run all tests
	@uv run pytest -v

test-quick:  ## ⚡ Run tests (quiet output)
	@uv run pytest -q

test-watch:  ## 👀 Run tests in watch mode
	@uv run pytest-watch

coverage:  ## 📊 Run tests with coverage report
	@uv run pytest --cov=accounts --cov=incidents --cov=shiptrack --cov-report=html --cov-report=term-missing
	@echo "✓ Coverage report generated (open htmlcov/index.html)"

coverage-report:  ## 📈 Show coverage statistics
	@uv run pytest --cov=accounts --cov=incidents --cov=shiptrack --cov-report=term-missing

# ============================================================================
# LINTING & CODE QUALITY
# ============================================================================

lint:  ## 🔍 Run all linters (ruff, mypy, bandit)
	@echo "Running linters..."
	@echo ""
	@echo "1️⃣  Ruff (style & complexity)..."
	@uv run ruff check . --exclude .venv,.claude,migrations
	@echo ""
	@echo "2️⃣  Format check (ruff format)..."
	@uv run ruff format --check . --exclude .venv,.claude,migrations
	@echo ""
	@echo "3️⃣  Type checking (mypy)..."
	@uv run mypy accounts incidents shiptrack manage.py --exclude migrations,.claude
	@echo ""
	@echo "4️⃣  Security scan (bandit)..."
	@uv run bandit -r accounts incidents shiptrack -c pyproject.toml -q
	@echo ""
	@echo "✓ All linters passed!"

type-check:  ## 🔤 Run type checker (mypy only)
	@echo "Type checking..."
	@uv run mypy accounts incidents shiptrack manage.py --exclude migrations

format-check:  ## ✨ Check code formatting (without fixing)
	@uv run ruff format --check . --exclude .venv,.claude,migrations

security:  ## 🔒 Run security scanner (bandit)
	@echo "Security scan..."
	@uv run bandit -r accounts incidents shiptrack -c pyproject.toml

format:  ## 🎨 Auto-format code with ruff
	@echo "Formatting code..."
	@uv run ruff format . --exclude .venv,.claude,migrations
	@uv run ruff check . --fix --exclude .venv,.claude,migrations
	@echo "✓ Code formatted!"

fix: format lint  ## 🔧 Format code and check linting

check:  ## ☑️  Django deployment checklist
	@echo "Running Django deployment checks..."
	@uv run python manage.py check --deploy

# ============================================================================
# STATIC FILES & COLLECTION
# ============================================================================

collect-static:  ## 📦 Collect static files for production
	@uv run python manage.py collectstatic --noinput
	@echo "✓ Static files collected"

collectstatic: collect-static  ## Alias for collect-static

# ============================================================================
# CLEANING UP
# ============================================================================

clean-pycache:  ## 🗑️  Remove Python cache files
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✓ Cleaned __pycache__ and .pyc files"

clean-cache:  ## 🗑️  Remove all cache directories (.pytest, .mypy, .ruff)
	@rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage 2>/dev/null || true
	@echo "✓ Cleaned cache directories"

clean-migrations:  ## 🗑️  List migration files (for review, doesn't delete)
	@find . -path "*/migrations/*.py" -not -name "__init__.py" -not -path "./.venv/*"

clean-all: clean-pycache clean-cache  ## 🗑️  Clean all cache and build artifacts
	@echo "✓ All caches cleaned"

# ============================================================================
# DOCKER
# ============================================================================

docker-up:  ## 🐳 Build and start Docker stack
	@docker compose up --build -d
	@echo "✓ Docker stack started"

docker-down:  ## 🛑 Stop Docker stack
	@docker compose down
	@echo "✓ Docker stack stopped"

docker-logs:  ## 📋 Tail Docker logs (web container)
	@docker compose logs -f web

docker-rebuild:  ## 🔨 Rebuild Docker images
	@docker compose build --no-cache
	@echo "✓ Docker images rebuilt"

# ============================================================================
# UTILITIES & SHORTCUTS
# ============================================================================

import-demo:  ## 📥 Import demo data (XLSX)
	@uv run python manage.py import_incidents

versions:  ## 📌 Show dependency versions
	@uv run pip list | grep -E "Django|djangorestframework|pytest|ruff|mypy"

status:  ## 📊 Show project status
	@echo "Project: ShipTrack"
	@echo "Django version: $$(uv run python -c 'import django; print(django.get_version())')"
	@echo "Python version: $$(python --version)"
	@echo "Database: SQLite (db.sqlite3)"
	@echo ""
	@echo "Test Suite: 70 tests"
	@echo "Code Linters: ✓ Ruff, MyPy, Bandit"
	@echo ""

info:  ## ℹ️  Show project information
	@echo "ShipTrack — Shipment Incident Tracker"
	@echo "======================================="
	@echo ""
	@echo "Quick Start:"
	@echo "  make install-dev    # Install dependencies"
	@echo "  make fresh-db       # Setup fresh database"
	@echo "  make up             # Start development server"
	@echo ""
	@echo "Common Commands:"
	@echo "  make test           # Run tests"
	@echo "  make lint           # Check code quality"
	@echo "  make format         # Auto-format code"
	@echo "  make migrate        # Apply migrations"
	@echo "  make seed           # Seed demo data"
	@echo ""
	@echo "Available Endpoints:"
	@echo "  http://localhost:8000/              # Main app"
	@echo "  http://localhost:8000/admin/        # Django admin"
	@echo "  http://localhost:8000/api/v1/       # REST API"
	@echo ""

.SILENT: info status
