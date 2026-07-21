# Backend
back-format:
	cd backend && uv run black . && uv run isort .

back-lint:
	cd backend && uv run flake8 . && uv run mypy .

back-test:
	cd backend && uv run pytest

back-install:
	cd backend && uv sync

back-dev:
	cd backend && uv sync && uv run alembic upgrade head && uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Frontend
front-format:
	cd frontend && npm run format

front-lint:
	cd frontend && npm run lint

front-build:
	cd frontend && npm run build

front-start:
	cd frontend && npm run start

front-dev:
	cd frontend && npm install && npm run dev

# Other
db-dev:
	docker compose -f ../docker-compose.yml -f docker-compose.dev.yml --env-file .env.docker up db; docker compose -f ../docker-compose.yml -f docker-compose.dev.yml --env-file .env.docker down

redis-dev:
	docker compose -f ../docker-compose.yml -f docker-compose.dev.yml --env-file .env.docker up redis; docker compose -f ../docker-compose.yml -f docker-compose.dev.yml --env-file .env.docker down

docker-dev:
	docker compose -f ../docker-compose.yml -f docker-compose.dev.yml --env-file .env.docker up --build; docker compose -f ../docker-compose.yml -f docker-compose.dev.yml --env-file .env.docker down

# Combined
format: front-format back-format
lint: front-lint back-lint
test: back-test
commit: format lint
