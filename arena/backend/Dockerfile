FROM python:3.12-slim

RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
    libcairo2 \
    fonts-liberation \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir "poetry==2.1.3"

WORKDIR /workspace/arena/backend

ENV POETRY_VIRTUALENVS_CREATE=false

COPY domain/pyproject.toml /workspace/domain/pyproject.toml
COPY domain/README.md /workspace/domain/README.md
COPY domain/champion_domain /workspace/domain/champion_domain
COPY arena/backend/pyproject.toml arena/backend/poetry.lock ./
RUN poetry install --no-interaction --no-ansi --no-root

COPY arena/backend /workspace/arena/backend

RUN chmod +x /workspace/arena/backend/docker-entrypoint.sh

RUN useradd -ms /bin/bash appuser
RUN mkdir -p /workspace/arena/backend/pdf_storage \
    && chown -R appuser:appuser /workspace/arena/backend/pdf_storage
USER appuser

ENTRYPOINT ["/workspace/arena/backend/docker-entrypoint.sh"]
