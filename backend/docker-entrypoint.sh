#!/bin/bash
set -euo pipefail

echo "[ENTRYPOINT] Running migrations..."
alembic upgrade head

echo "[ENTRYPOINT] Creating default user..."
python -m src.init_data

echo "[ENTRYPOINT] Starting app..."
exec uvicorn src.main:app \
  --workers "${BACKEND_WORKERS:-1}" \
  --host 0.0.0.0 \
  --port 8000 \
  --log-level info
