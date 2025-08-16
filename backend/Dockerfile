FROM python:3.12-slim

RUN pip install --no-cache-dir poetry

RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
    libcairo2 \
    fonts-liberation && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV POETRY_VIRTUALENVS_CREATE=false

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-interaction --no-ansi

COPY . .

RUN chmod +x /app/docker-entrypoint.sh

ENTRYPOINT ["/app/docker-entrypoint.sh"]
