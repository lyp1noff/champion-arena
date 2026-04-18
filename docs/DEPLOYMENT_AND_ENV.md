# Deployment and env

This repo contains two separately deployed applications:

- `arena` - central system
- `tatami` - local tatami node (`backend` + `frontend` + `outbox`)

They share `domain`, but they do not share runtime or deployment.

## GitHub Actions

Only workflows in the repo-root `.github/workflows` directory are active.

Active workflows:

- `.github/workflows/ci-docker.yml` - builds and redeploys `arena`
- `.github/workflows/tatami-docker.yml` - builds and pushes `tatami`

### Arena Actions env

`arena` workflow uses:

- repo/environment vars:
    - `NEXT_PUBLIC_BACKEND_URL`
    - `NEXT_PUBLIC_CDN_URL`
    - `NEXT_PUBLIC_ANALYTICS_URL`
    - `NEXT_PUBLIC_ANALYTICS_ID`
- repo/environment secrets:
    - `PORTAINER_STACK_WEBHOOK`

### Tatami Actions env

`tatami` workflow does not redeploy anything automatically.

`tatami/frontend` currently does not require build-time args when served behind nginx on `/api`.

## Arena runtime env

Use `arena/example.env` as the template.

Required:

- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`
- `JWT_SECRET`
- `SERVICE_TOKEN`

Required when using Redis/websocket outside local dev:

- `REDIS_PORT`

Optional / deployment-specific:

- `FRONTEND_PORT`
- `BACKEND_PORT`
- `DB_PORT`
- `FRONTEND_URL`
- `DEV_MODE`
- `BACKEND_WORKERS`
- `R2_ACCESS_KEY_ID`
- `R2_SECRET_ACCESS_KEY`
- `R2_BUCKET_NAME`
- `R2_ENDPOINT`
- `R2_REGION`
- `NEXT_PUBLIC_BACKEND_URL`
- `NEXT_PUBLIC_CDN_URL`
- `NEXT_PUBLIC_ANALYTICS_URL`
- `NEXT_PUBLIC_ANALYTICS_ID`

## Tatami runtime env

Use `tatami/example.env` as the template.

Required:

- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`
- `EXTERNAL_API_URL` - arena API base URL, usually with `/api`
- `EXTERNAL_API_TOKEN` - service token accepted by arena
- `EDGE_ID` - unique per physical tatami node

Recommended:

- `LOG_LEVEL`
- `PROCESSING_INTERVAL`
- `HTTP_TIMEOUT`
- `BATCH_SIZE`

Optional:

- `DEV_MODE`
- `FRONTEND_PORT`
- `BACKEND_PORT`
- `NEXT_PUBLIC_BACKEND_URL` - only for standalone frontend dev without nginx

## Docker compose

### Arena

- prod-ish stack: root `docker-compose.yml`
- local build override: `arena/docker-compose.dev.yml`

Run:

```bash
docker compose --env-file arena/.env.docker -f docker-compose.yml -f arena/docker-compose.dev.yml up --build
```

### Tatami

- prod-ish stack: `tatami/docker-compose.yml`
- local build override: `tatami/docker-compose.dev.yml`

Run:

```bash
cd tatami
docker compose --env-file .env.docker -f docker-compose.yml -f docker-compose.dev.yml up --build
```

Notes:

- `arena` keeps the main compose in the repo root because Portainer expects it there
- `arena/docker-compose.dev.yml` is only the local override layer
- `tatami` compose now hardcodes internal DB host as `db` for `backend` and `outbox`
- `EDGE_ID` must be different for each tatami node
- `outbox` pushes to `EXTERNAL_API_URL/sync/upserts` through the `tatami` backend queue records
