FROM ghcr.io/astral-sh/uv:python3.12-trixie-slim AS builder

WORKDIR /workspace

ENV UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/workspace/.venv

COPY .python-version pyproject.toml uv.lock ./
COPY domain/pyproject.toml domain/README.md /workspace/domain/
COPY domain/champion_domain /workspace/domain/champion_domain
COPY arena/backend/pyproject.toml /workspace/arena/backend/pyproject.toml
COPY tatami/backend/pyproject.toml /workspace/tatami/backend/pyproject.toml
RUN uv sync --locked --no-dev --no-editable --package champion

FROM python:3.12-slim-trixie

RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
    libcairo2 \
    fonts-liberation \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace/arena/backend

ENV PATH="/workspace/.venv/bin:$PATH"

COPY --from=builder /workspace/.venv /workspace/.venv
COPY arena/backend /workspace/arena/backend

RUN chmod +x /workspace/arena/backend/docker-entrypoint.sh

RUN useradd -ms /bin/bash appuser
RUN mkdir -p /workspace/arena/backend/pdf_storage \
    && chown -R appuser:appuser /workspace/arena/backend/pdf_storage
USER appuser

ENTRYPOINT ["/workspace/arena/backend/docker-entrypoint.sh"]
