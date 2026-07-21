FROM ghcr.io/astral-sh/uv:python3.12-trixie-slim AS builder

WORKDIR /workspace/arena/backend

ENV UV_LINK_MODE=copy

COPY domain/pyproject.toml /workspace/domain/pyproject.toml
COPY domain/README.md /workspace/domain/README.md
COPY domain/champion_domain /workspace/domain/champion_domain
COPY arena/backend/pyproject.toml arena/backend/uv.lock ./
RUN uv sync --locked --no-dev --no-editable

FROM python:3.12-slim

RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
    libcairo2 \
    fonts-liberation \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace/arena/backend

ENV PATH="/workspace/arena/backend/.venv/bin:$PATH"

COPY --from=builder /workspace/arena/backend/.venv ./.venv
COPY arena/backend /workspace/arena/backend

RUN chmod +x /workspace/arena/backend/docker-entrypoint.sh

RUN useradd -ms /bin/bash appuser
RUN mkdir -p /workspace/arena/backend/pdf_storage \
    && chown -R appuser:appuser /workspace/arena/backend/pdf_storage
USER appuser

ENTRYPOINT ["/workspace/arena/backend/docker-entrypoint.sh"]
