FROM python:3.12-slim

RUN pip install --no-cache-dir poetry

WORKDIR /workspace/tatami/backend

ENV POETRY_VIRTUALENVS_CREATE=false

COPY domain/pyproject.toml /workspace/domain/pyproject.toml
COPY domain/README.md /workspace/domain/README.md
COPY domain/champion_domain /workspace/domain/champion_domain
COPY tatami/backend/pyproject.toml tatami/backend/poetry.lock ./
RUN poetry install --no-interaction --no-ansi --no-root

COPY tatami/backend /workspace/tatami/backend

CMD ["gunicorn", "src.main:app", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
