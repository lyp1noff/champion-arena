FROM ghcr.io/astral-sh/uv:python3.12-trixie-slim AS builder

WORKDIR /workspace/tatami/backend

ENV UV_LINK_MODE=copy

COPY domain/pyproject.toml /workspace/domain/pyproject.toml
COPY domain/README.md /workspace/domain/README.md
COPY domain/champion_domain /workspace/domain/champion_domain
COPY tatami/backend/pyproject.toml tatami/backend/uv.lock ./
RUN uv sync --locked --no-dev --no-editable

FROM python:3.12-slim

WORKDIR /workspace/tatami/backend

ENV PATH="/workspace/tatami/backend/.venv/bin:$PATH"

COPY --from=builder /workspace/tatami/backend/.venv ./.venv
COPY tatami/backend /workspace/tatami/backend

CMD ["gunicorn", "src.main:app", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
