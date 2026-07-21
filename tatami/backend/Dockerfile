FROM ghcr.io/astral-sh/uv:python3.12-trixie-slim AS builder

WORKDIR /workspace

ENV UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/workspace/.venv

COPY .python-version pyproject.toml uv.lock ./
COPY domain/pyproject.toml domain/README.md /workspace/domain/
COPY domain/champion_domain /workspace/domain/champion_domain
COPY arena/backend/pyproject.toml /workspace/arena/backend/pyproject.toml
COPY tatami/backend/pyproject.toml /workspace/tatami/backend/pyproject.toml
RUN uv sync --locked --no-dev --no-editable --package champion-tatami

FROM python:3.12-slim-trixie

WORKDIR /workspace/tatami/backend

ENV PATH="/workspace/.venv/bin:$PATH"

COPY --from=builder /workspace/.venv /workspace/.venv
COPY tatami/backend /workspace/tatami/backend

CMD ["gunicorn", "src.main:app", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
