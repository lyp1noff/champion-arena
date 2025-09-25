FROM python:3.12-slim

RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
    libcairo2 \
    fonts-liberation \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir "poetry==2.1.3"

WORKDIR /app

ENV POETRY_VIRTUALENVS_CREATE=false

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-interaction --no-ansi --no-root

COPY . .

RUN chmod +x /app/docker-entrypoint.sh

RUN useradd -ms /bin/bash appuser
RUN mkdir -p /app/pdf_storage \
    && chown -R appuser:appuser /app/pdf_storage
USER appuser

ENTRYPOINT ["/app/docker-entrypoint.sh"]
