# ShipTrack

A multi-user web app for tracking shipment incidents (damage, missing labels,
mis-routed deliveries, etc.). Carrier-agnostic, OWASP-hardened, deployable
with one `docker compose up`. Originally seeded from an Excel workbook —
the importer still accepts the legacy column headers.

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
- **OWASP-hardened**: Argon2 hashing, HSTS, CSP, Permissions-Policy,
  X-Frame-Options DENY, secure cookies, brute-force lockout
  (django-axes), rate-limited importer, file-size & content-type guards,
  CSRF on, SQL injection avoided via the ORM, no DEBUG by default,
  secrets via env, runs as non-root in the container, internal-only DB
  network in compose.
- **pytest** suite covering models, views, RBAC, security headers, CSRF,
  password validators, REST API, and the importer.

## Quickstart

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

## Tests

```bash
uv sync
uv run pytest -q
```

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
