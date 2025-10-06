#!/bin/bash
set -euo pipefail

echo "[ENTRYPOINT] Running migrations..."
alembic upgrade head

echo "[ENTRYPOINT] Creating default user..."
python -m src.init_data

echo "[ENTRYPOINT] Starting app..."
exec gunicorn src.main:app \
  -k uvicorn.workers.UvicornWorker \
  --workers "${GUNICORN_WORKERS:-1}" \
  --bind 0.0.0.0:8000 \
  --error-logfile - \
  --log-level info
