#!/bin/sh
# Container entrypoint. Runs schema migrations, seeds groups + (optional)
# superuser, optionally imports a bundled sample spreadsheet, then execs
# whatever the CMD told us to run.
set -eu

echo "[entrypoint] running migrations..."
python manage.py migrate --noinput

echo "[entrypoint] seeding groups / superuser (if env set)..."
python manage.py seed_demo

echo "[entrypoint] collecting static..."
python manage.py collectstatic --noinput

# If SEED_SAMPLE_DATA=1 and the DB has no incidents yet, import any spreadsheet
# placed in /app/sample_data/. Idempotent across restarts.
if [ "${SEED_SAMPLE_DATA:-0}" = "1" ]; then
    incident_count="$(python manage.py shell -c 'from incidents.models import Incident; print(Incident.objects.count())' 2>/dev/null || echo 0)"
    if [ "$incident_count" = "0" ]; then
        sample_file="$(find /app/sample_data -maxdepth 1 -type f \( -name '*.xlsm' -o -name '*.xlsx' -o -name '*.csv' \) 2>/dev/null | head -1 || true)"
        if [ -n "$sample_file" ]; then
            echo "[entrypoint] empty DB - importing $sample_file"
            python manage.py import_incidents "$sample_file" || \
                echo "[entrypoint] WARNING: sample import failed; continuing"
        else
            echo "[entrypoint] SEED_SAMPLE_DATA=1 but no sample file found in /app/sample_data; skipping"
        fi
    else
        echo "[entrypoint] DB already has $incident_count incidents; skipping sample import"
    fi
fi

echo "[entrypoint] starting: $*"
exec "$@"
