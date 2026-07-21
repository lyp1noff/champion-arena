# Backend
back-format:
	cd backend && uv run black . && uv run isort .

back-lint:
	cd backend && uv run flake8 . && uv run mypy .

back-test:
	cd backend && uv run pytest

back-install:
	cd backend && uv sync --all-packages --all-groups

back-dev:
	cd backend && uv sync --all-packages --all-groups && uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8001

# Frontend
front-format:
	cd frontend && npm run format

front-lint:
	cd frontend && npm run lint

front-build:
	cd frontend && npm run build

front-dev:
	cd frontend && npm install && npm run dev

# Outbox
outbox-dev:
	cd outbox && go run cmd/outbox-worker/main.go

# Other
db:
	docker compose --env-file .env up db

docker-dev:
	docker compose -f docker-compose.yml --env-file .env.docker up --build && docker compose down

# Combined
format: front-format back-format
lint: front-lint back-lint
test: back-test
commit: format lint
