# ShipTrack — common tasks. Run `make` (or `make help`) to see all targets.
.DEFAULT_GOAL := help

.PHONY: help up sync migrate seed test lint format check fix \
        docker-up docker-down docker-logs collectstatic shell

help:  ## Show this help.
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	  | awk 'BEGIN{FS=":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

up:  ## Start the dev server (browser opens automatically). Ctrl+C to stop.
	@bash scripts/launch.sh

sync:  ## Install / refresh dependencies.
	@uv sync

migrate:  ## Apply Django migrations.
	@uv run python manage.py migrate

seed:  ## Seed canonical groups + (optional) DJANGO_SUPERUSER_* admin.
	@uv run python manage.py seed_demo

shell:  ## Open a Django shell.
	@uv run python manage.py shell

collectstatic:  ## Build /staticfiles for production.
	@uv run python manage.py collectstatic --noinput

test:  ## Run the pytest suite (SQLite, no Postgres needed).
	@uv run pytest -q

lint:  ## Run all linters (ruff, ruff format check, mypy, bandit).
	@uv run ruff check .
	@uv run ruff format --check .
	@uv run bandit -r accounts incidents shiptrack -c pyproject.toml -q
	@uv run mypy accounts incidents shiptrack manage.py

format:  ## Auto-format code with ruff.
	@uv run ruff format .
	@uv run ruff check . --fix

fix: format lint  ## Format then lint.

check:  ## Django deploy checklist.
	@uv run python manage.py check --deploy

docker-up:  ## Build and start the full Docker stack.
	@docker compose up --build -d

docker-down:  ## Stop the Docker stack.
	@docker compose down

docker-logs:  ## Tail the web container logs.
	@docker compose logs -f web
