# Mtaani Express Ledger — run `just` to list recipes.

set dotenv-load := false

api_url := "http://localhost:8000"

# List recipes
default:
    @just --list --unsorted

# --- Stack -------------------------------------------------------------------

# Build and start db, api and worker
up:
    docker compose up -d --build

# Start only db + api
api:
    docker compose up -d --build api

# Start only db + worker
worker:
    docker compose up -d --build worker

# Stop the stack (keeps the database volume)
down:
    docker compose down

# Stop the stack and delete the database volume
nuke:
    docker compose down -v

# Show service status
ps:
    docker compose ps

# Follow logs (all services, or one: `just logs worker`)
logs *service:
    docker compose logs -f --tail 50 {{service}}

# Open a psql shell on the compose database
psql:
    docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'

# Run the API on the host with auto-reload (needs `just db`)
dev:
    uv run uvicorn app.main:app --reload --port 8000

# Start only the database
db:
    docker compose up -d db

# --- Database migrations ------------------------------------------------------

# Apply migrations (default: head)
migrate target="head":
    docker compose run --rm api alembic upgrade {{target}}

# Roll back migrations (default: base)
rollback target="base":
    docker compose run --rm api alembic downgrade {{target}}

# Create a new migration: `just revision "add accounts"`
revision message:
    docker compose run --rm -v "$PWD/migrations:/app/migrations" -u "$(id -u):$(id -g)" \
        api alembic revision -m "{{message}}"

# --- Checks --------------------------------------------------------------------

# Hit both health endpoints
health:
    curl -fsS {{api_url}}/health && echo
    curl -fsS {{api_url}}/health/db && echo

# Run tests (extra args pass through: `just test -k worker`)
test *args:
    uv run pytest -q {{args}}

# Lint and check formatting
lint:
    uv run ruff check .
    uv run ruff format --check .

# Auto-fix lint and format
fmt:
    uv run ruff check --fix .
    uv run ruff format .

# Lint + tests
check: lint test

# Full end-to-end verification from a fresh build
verify:
    #!/usr/bin/env bash
    set -euo pipefail
    step() { printf '\n\033[1m== %s\033[0m\n' "$*"; }
    step "build and start";        docker compose up -d --build --wait
    step "status";                 docker compose ps
    step "health";                 just health
    step "migrate up";             just migrate
    step "migrate down";           just rollback
    step "migrate up again";       just migrate
    step "worker heartbeat (UTC)"; docker compose logs worker --tail 5
    step "worker clean shutdown"
    docker compose stop worker
    logs=$(docker compose logs worker --tail 3); echo "$logs"
    if grep -q Traceback <<<"$logs"; then echo "traceback in worker logs" >&2; exit 1; fi
    docker compose start worker >/dev/null
    step "lint";                   just lint
    step "tests";                  just test
    step "git";                    git status --short; git log --oneline -5
    printf '\n\033[32mverify: all checks passed\033[0m\n'
