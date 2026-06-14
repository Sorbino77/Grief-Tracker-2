# ShipTrack

[![CI](https://github.com/OWNER/REPO/actions/workflows/ci.yml/badge.svg)](https://github.com/OWNER/REPO/actions/workflows/ci.yml)
[![Release](https://github.com/OWNER/REPO/actions/workflows/release.yml/badge.svg)](https://github.com/OWNER/REPO/actions/workflows/release.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.14](https://img.shields.io/badge/python-3.14-blue.svg)](https://www.python.org/)
[![Django 6.0](https://img.shields.io/badge/django-6.0-092E20.svg)](https://www.djangoproject.com/)

A multi-user web app for tracking shipment incidents (damage, missing labels,
mis-routed deliveries, etc.). Carrier-agnostic, OWASP-hardened, deployable
with one `docker compose up`, one-click on Render or Fly.io, or as a
pre-built image from GHCR. Originally seeded from an Excel workbook — the
importer still accepts the legacy column headers.

> **Replace `OWNER/REPO`** in the badge URLs above with your GitHub
> `<owner>/<repo>` once you push the project (otherwise the badges 404).

## Quick Links

📚 **Documentation:**
- [`ACCESSIBILITY.md`](ACCESSIBILITY.md) — 11 gaming-style accessibility features
- [`ACCESSIBILITY_QUICK_START.md`](ACCESSIBILITY_QUICK_START.md) — Quick reference
- [`MAKEFILE_GUIDE.md`](MAKEFILE_GUIDE.md) — 40+ development commands
- [`DOCUMENTATIE.md`](DOCUMENTATIE.md) — Full Dutch documentation

🎯 **Key Stats:**
- ✅ 70 tests passing (100% pass rate)
- ✅ 100% type coverage (mypy clean)
- ✅ 0 security issues (bandit clean)
- ✅ 49 Python files (2,996 lines of code)
- ✅ WCAG 2.1 AAA compliant
- ✅ 11 accessibility features
- ✅ 40+ Makefile commands

## Deploy from GitHub

Three flavours:

### Option A — Render (free tier, click-and-go)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/OWNER/REPO)

Render reads `render.yaml` and provisions a managed Postgres 16 + Redis 7 +
Dockerised web service in the same private network. The first build sets a
strong `DJANGO_SECRET_KEY` automatically; you only have to fill in the
`DJANGO_SUPERUSER_*` trio in the dashboard to bootstrap the first admin.

### Option B — Fly.io (global edge, $5/mo and up)

```bash
flyctl launch --copy-config --name <YOUR_APP_NAME>
flyctl postgres create --name <YOUR_APP_NAME>-db
flyctl postgres attach <YOUR_APP_NAME>-db
flyctl secrets set DJANGO_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(64))')"
flyctl deploy
```

`fly.toml` is already in the repo (Amsterdam region, auto-stop machines, HTTPS
redirect, healthcheck on `/healthz/`).

### Option C — Anywhere with Docker (pull from GHCR)

Once you push to GitHub, the **Release** workflow builds a multi-arch image
(`linux/amd64` + `linux/arm64`) and publishes it to
`ghcr.io/<owner>/<repo>:latest`. Pull it on any host:

```bash
docker run -d --name shiptrack \
  -p 8000:8000 \
  -e DJANGO_SECRET_KEY=$(python -c "import secrets;print(secrets.token_urlsafe(64))") \
  -e DJANGO_DEBUG=False \
  -e DJANGO_ALLOWED_HOSTS=your.domain.com \
  -e USE_POSTGRES=True \
  -e POSTGRES_HOST=db.example.com \
  -e POSTGRES_DB=shiptrack -e POSTGRES_USER=shiptrack -e POSTGRES_PASSWORD=*** \
  ghcr.io/OWNER/REPO:latest
```

### Option D — `docker compose up` (your own host)

```bash
git clone https://github.com/OWNER/REPO.git && cd REPO
cp .env.example .env       # edit secrets
docker compose up --build -d
# http://localhost:8080
```

## What's wired up in CI/CD

- **`ci.yml`** runs on every push and PR:
  - `ruff check` + `ruff format --check`
  - `bandit -r accounts incidents shiptrack`
  - `mypy` with django-stubs / drf-stubs
  - `pytest --cov`
  - `manage.py check --deploy` against prod-like env
  - Builds the Docker image and verifies `/healthz/` returns 200
- **`release.yml`** runs on push to `main` and on `v*.*.*` tags:
  - Builds multi-arch Docker images (`amd64` + `arm64`)
  - Pushes to GHCR with semver / branch / sha tags
  - Generates SBOM + provenance attestations
- **`dependabot.yml`** opens weekly PRs for Python deps, GitHub Actions, and
  the Docker base image. Django and security tools are grouped to keep PR
  noise down.

## Features

- **Incident CRUD** — primary reference, shipment ID, transport order ref,
  supplier, country, location, carrier, issue type, dates, image flag,
  causing party, status, notes, plus audit fields. Uniqueness constraint on
  `(primary_ref, issue_type)` keeps re-imports idempotent.
- **Multi-user with roles** — Admin, Editor, Viewer. Admins can change
  roles in the UI. Username/password sign-in plus pluggable Google /
  Microsoft SSO via [django-allauth].
- **Easy import** — UI form **and** CLI for `.xlsx`, `.xlsm`, `.csv`. The
  importer is forgiving about column-name variations (recognises both
  `Primary Ref` and the legacy `K&N REF` / `KN REF` / `Kuehne ref`),
  idempotent on re-import, supports dry-run, and reports per-row errors.
- **Analytics page** — pivot-style breakdowns by carrier, issue type,
  causing party, status, and year.
- **REST API** — `/api/v1/incidents/` etc. with filter / search / ordering,
  role enforcement, throttling, and TokenAuth or session auth.
- **♿ Gaming-style Accessibility** — 11 accessibility features inspired
  by modern gaming standards: high contrast mode, dyslexia-friendly font,
  font size scaling (100%-175%), colorblind modes (4 types), reduced motion,
  large touch targets, keyboard navigation hints, simplified layout, reading
  guide, captions, and screen reader mode. WCAG 2.1 AAA compliant. See
  [`ACCESSIBILITY.md`](ACCESSIBILITY.md) for details.
- **OWASP-hardened**: Argon2 hashing, HSTS, CSP, Permissions-Policy,
  X-Frame-Options DENY, secure cookies, brute-force lockout
  (django-axes), rate-limited importer, file-size & content-type guards,
  CSRF on, SQL injection avoided via the ORM, no DEBUG by default,
  secrets via env, runs as non-root in the container, internal-only DB
  network in compose.
- **Production-grade code quality** — 100% type coverage (mypy), code
  linting (ruff), security scanning (bandit), 70+ test suite with coverage
  reports. All checks automated in CI/CD.
- **Comprehensive Makefile** — 40+ commands for development, testing,
  linting, database, Docker, and utilities. Run `make help` to see all
  shortcuts. See [`MAKEFILE_GUIDE.md`](MAKEFILE_GUIDE.md) for details.
- **pytest** suite covering models, views, RBAC, security headers, CSRF,
  password validators, REST API, accessibility settings, and the importer.

## ♿ Accessibility (Gaming-Style Options)

ShipTrack includes **11 accessibility features** inspired by modern gaming
industry standards (Xbox, PlayStation, Game Accessibility Guidelines). All
settings are WCAG 2.1 AAA compliant and auto-create for new users.

**Visual** (4 features): high contrast mode, dyslexia-friendly font, font
size scaling (100%-175%), colorblind modes (Protanopia, Deuteranopia,
Tritanopia, Achromatopsia).

**Motor** (3 features): reduced motion, large touch targets (48x48px),
keyboard navigation hints.

**Cognitive** (2 features): simplified layout, reading guide.

**Audio/Content** (2 features): captions, screen reader mode.

**Access Settings:**
- Click ♿ button in navbar (when logged in)
- Press `Alt+A` keyboard shortcut
- Visit `/u/accessibility/`

See [`ACCESSIBILITY.md`](ACCESSIBILITY.md) and
[`ACCESSIBILITY_QUICK_START.md`](ACCESSIBILITY_QUICK_START.md) for complete
documentation.

## Easy launch

Three ways, pick whichever fits:

| Platform | One-shot command                  | What it does |
|----------|----------------------------------|--------------|
| **Windows** | **Double-click `start.bat`**   | Syncs deps → checks Postgres → migrates → seeds → opens the browser → starts the dev server |
| **macOS / Linux** | `make up`                | Same as above (via `scripts/launch.sh`) |
| **Any** (full prod-like stack) | `docker compose up --build -d` | Postgres + Redis + Django + nginx on port 8080 |

**For day-to-day commands**, `make help` lists 40+ shortcuts:

```bash
# Development
make up                 # Start dev server
make test               # Run 70 tests
make lint               # Ruff + MyPy + Bandit
make format             # Auto-format code
make accessibility      # 🎮 Open accessibility settings

# Database
make migrate            # Apply migrations
make fresh-db           # Reset + migrate + seed
make shell              # Django shell
make admin-user         # Create superuser

# Docker
make docker-up          # Run full stack
make docker-logs        # View logs

# And 25+ more...
```

See [`MAKEFILE_GUIDE.md`](MAKEFILE_GUIDE.md) for the complete reference.

## Production deploy with Docker

```bash
# 1. Configure secrets (NEVER commit .env)
cp .env.example .env
# Edit DJANGO_SECRET_KEY (50 random bytes), POSTGRES_PASSWORD, and the
# optional DJANGO_SUPERUSER_* trio if you want a bootstrap admin.

# 2. (Optional) auto-import a sample spreadsheet on first boot.
#    Drop any .xlsx/.xlsm/.csv file into ./sample_data/ and:
echo "SEED_SAMPLE_DATA=1" >> .env

# 3. Build and run
docker compose up --build -d

# 4. Open the app
#    http://localhost:8080
```

If you set `DJANGO_SUPERUSER_*`, sign in with those credentials and head to
`/u/users/` to invite teammates and assign their role. Otherwise, create
the first admin manually:

```bash
docker compose exec web python manage.py createsuperuser
```

## Local development (with `uv`)

```bash
uv sync                                # creates .venv from pyproject.toml + uv.lock
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

Test-mode env defaults are picked up automatically when pytest is detected,
so you can also just run `uv run pytest -q`.

## Importing data

**From the UI** (Editor or Admin):  *Import* → choose your `.xlsx` /
`.xlsm` / `.csv` → optionally tick *Dry run* to validate without writing.

**From the CLI**:

```bash
# Modern spreadsheet (header row 1, sheet "Incidents")
docker compose exec web python manage.py import_incidents \
    "/app/sample_data/incidents.xlsx"

# Legacy K+N workbook (header row 10, sheet "Grief"). Column names like
# `K&N REF`, `KN REF`, `Kuehne ref` are still recognised.
docker compose exec web python manage.py import_incidents \
    "/app/sample_data/Grief 003.xlsm" --sheet Grief --header-row 10
```

Re-running is safe — rows are matched on `(primary_ref, issue_type)` and
updated rather than duplicated.

## Code Quality & Testing

**70 comprehensive tests** covering models, views, API, RBAC, security,
importer, and accessibility features. All tests passing.

```bash
# Run all tests
uv run pytest -q

# With coverage report
uv run pytest --cov=accounts --cov=incidents --cov=shiptrack --cov-report=html

# Watch mode (auto-run on file change)
uv run pytest-watch
```

**Linting & Type Checking:**

```bash
# Run all linters (ruff, mypy, bandit)
make lint

# Or individually:
uv run ruff check .              # Style & complexity
uv run mypy . --exclude=migrations  # Type checking (100% clean)
uv run bandit -r accounts incidents shiptrack  # Security scanning

# Auto-format code
make format
```

**Continuous Integration** (`ci.yml`):
- Ruff style checking + auto-format verification
- MyPy type checking (100% coverage, no errors)
- Bandit security scanning
- pytest with coverage
- Django deployment checklist (`manage.py check --deploy`)
- Docker image build & health check

Tests run against an SQLite in-memory DB so no Postgres is required.

## Architecture

```
shiptrack/         Django project (settings + URLs)
accounts/          Custom user, roles, permission helpers
incidents/         Domain models, views, forms, REST API, importer
templates/         Server-rendered HTML
static/css/        One small stylesheet (no CDN dependencies)
tests/             pytest suite (models, views, API, security, importer)
nginx/             Reverse-proxy config
sample_data/       Drop spreadsheets here for first-boot seeding
scripts/           Operator helpers (e.g. local Postgres password reset)
```

## OWASP coverage cheat-sheet

| OWASP Top 10 (2021)               | Where it's handled |
| --------------------------------- | ------------------ |
| A01 Broken Access Control         | `accounts/permissions.py`, `@role_required`, DRF perms, login-required everywhere except `/healthz/` |
| A02 Cryptographic Failures        | Argon2 hasher, HSTS, secure/httponly cookies, secrets via env |
| A03 Injection                     | ORM-only queries, parameterised search, Django auto-escaping |
| A04 Insecure Design               | Deny-by-default permissions, atomic importer, dry-run flag |
| A05 Security Misconfiguration     | DEBUG off, no default secret, CSP, Permissions-Policy, non-root container, internal DB network |
| A06 Vulnerable Components         | Pinned `pyproject.toml` + `uv.lock`, slim base image |
| A07 Identification & Auth Failures| `django-axes` lockout, 12-char password validator, allauth rate limits |
| A08 Data Integrity Failures       | CSRF middleware, signed sessions, idempotent importer |
| A09 Logging & Monitoring          | Structured stdout logging, axes records lockouts |
| A10 SSRF                          | No user-supplied outbound URLs |

## Production checklist

Before exposing this on the public internet:

1. Put TLS in front of nginx (e.g. with Caddy, Traefik, or certbot).
2. Set `DJANGO_DEBUG=False`, `DJANGO_SECURE_SSL_REDIRECT=True`,
   `DJANGO_SESSION_COOKIE_SECURE=True`, `DJANGO_CSRF_COOKIE_SECURE=True`,
   `DJANGO_SECURE_HSTS_SECONDS=31536000`.
3. Generate a real `DJANGO_SECRET_KEY` (50 random bytes).
4. Restrict `DJANGO_ALLOWED_HOSTS` and `DJANGO_CSRF_TRUSTED_ORIGINS` to
   your domain.
5. Take regular `pg_dump` backups of the `db` volume.
