#!/bin/bash
set -euo pipefail

if [[ "${WAIT_FOR_DB:-true}" == "true" ]]; then
    echo "[ENTRYPOINT] Waiting for database..."
    until alembic upgrade head 2>/dev/null; do
#    until alembic upgrade head; do
        echo "DB not ready, retrying in 2s..."
        sleep 2
    done
    echo "[ENTRYPOINT] DB ready and migrations applied."
else
    echo "[ENTRYPOINT] Skipping wait for DB."
    alembic upgrade head
fi

echo "[ENTRYPOINT] Creating default user..."
python -m src.init_data

exec gunicorn src.main:app \
    -k uvicorn.workers.UvicornWorker \
    --workers "${GUNICORN_WORKERS:-1}" \
    --bind 0.0.0.0:8000
