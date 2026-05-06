#!/usr/bin/env bash
# ShipTrack launcher (macOS / Linux). Use `make up` or `bash scripts/launch.sh`.
set -euo pipefail
cd "$(dirname "$0")/.."

bind="${SHIPTRACK_BIND:-127.0.0.1}"
port="${SHIPTRACK_PORT:-8000}"
url="http://${bind}:${port}"

step() { printf "\033[36m[launch] %s\033[0m\n" "$*"; }
ok()   { printf "\033[32m[launch] %s\033[0m\n" "$*"; }
err()  { printf "\033[31m[launch] %s\033[0m\n" "$*" >&2; }

if ! command -v uv >/dev/null 2>&1; then
    err "uv not found. Install from https://docs.astral.sh/uv/"
    exit 1
fi

step "syncing dependencies..."
uv sync --quiet

# Postgres reachability check (only when USE_POSTGRES=True in .env)
if [ -f .env ] && grep -qE '^[[:space:]]*USE_POSTGRES[[:space:]]*=[[:space:]]*True' .env; then
    step "checking Postgres on localhost:5432..."
    if ! (echo > "/dev/tcp/localhost/5432") 2>/dev/null; then
        err "Postgres not reachable on localhost:5432."
        echo "       Either start it, or set USE_POSTGRES=False in .env to use SQLite."
        exit 1
    fi
fi

step "applying migrations..."
uv run python manage.py migrate --noinput

step "seeding groups + admin..."
uv run python manage.py seed_demo

# Open the browser when /healthz/ responds, in the background.
(
    deadline=$(( $(date +%s) + 30 ))
    while [ "$(date +%s)" -lt "$deadline" ]; do
        if curl -fsS "$url/healthz/" >/dev/null 2>&1; then
            if command -v xdg-open >/dev/null 2>&1; then xdg-open "$url" >/dev/null 2>&1
            elif command -v open    >/dev/null 2>&1; then open    "$url" >/dev/null 2>&1
            fi
            break
        fi
        sleep 0.4
    done
) &

echo
ok "starting ShipTrack at $url"
ok "press Ctrl+C to stop"
echo
exec uv run python manage.py runserver "${bind}:${port}"
