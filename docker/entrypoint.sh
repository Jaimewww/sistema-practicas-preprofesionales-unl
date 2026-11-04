#!/bin/sh
# Prepares the database and loads demo data before starting the backend.
set -eu

if [ -n "${POSTGRES_HOST:-}" ]; then
    echo "entrypoint: waiting for PostgreSQL at ${POSTGRES_HOST}:${POSTGRES_PORT:-5432}"
    python - <<'PY'
import os, socket, sys, time

host = os.environ["POSTGRES_HOST"]
port = int(os.environ.get("POSTGRES_PORT", "5432"))
for _ in range(30):
    try:
        socket.create_connection((host, port), timeout=2).close()
        sys.exit(0)
    except OSError:
        time.sleep(1)
sys.exit("entrypoint: PostgreSQL is not reachable")
PY
fi

echo "entrypoint: applying migrations"
python manage.py migrate --noinput

# The seed command arrives with the persistence layer (#76); skip it until then.
if python manage.py help seed >/dev/null 2>&1; then
    echo "entrypoint: loading demo data"
    python manage.py seed
else
    echo "entrypoint: no seed command yet, skipping demo data"
fi

exec "$@"
