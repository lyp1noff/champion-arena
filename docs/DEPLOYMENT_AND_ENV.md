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
- `CLOUDFLARE_TUNNEL_TOKEN` - token for the remotely managed Cloudflare Tunnel

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
- `OUTBOX_POLL_INTERVAL_SECONDS`
- `OUTBOX_HTTP_TIMEOUT_SECONDS`
- `OUTBOX_LEASE_SECONDS`

Optional:

- `DEV_MODE`
- `FRONTEND_PORT`
- `BACKEND_PORT`
- `NEXT_PUBLIC_BACKEND_URL` - only for standalone frontend dev without nginx

## Docker compose

### Arena

- prod-ish stack: root `docker-compose.yml`
- local build override: `arena/docker-compose.dev.yml`

The production request path is:

```text
Cloudflare -> cloudflared -> nginx -> frontend/backend
```

Create a remotely managed tunnel in Cloudflare and configure its public
hostname to use `http://nginx:80` as the service URL. Put the tunnel token in
the deployment environment as `CLOUDFLARE_TUNNEL_TOKEN`.

The production nginx configuration is baked into the `champion-nginx` image so
that a Portainer Git stack does not depend on host bind mounts. The service
intentionally has no published host port. Once the tunnel has been verified,
stop the host nginx service and block inbound TCP ports 80 and 443 at the
host/provider firewall. Keep outbound TCP/UDP port 7844 available for
`cloudflared` and do not remove SSH access until the tunnel deployment has been
verified.

Cloudflare Access is not required: the application remains public through the
tunnel while direct access to the origin is closed.

Run:

```bash
docker compose --env-file arena/.env.docker -f docker-compose.yml -f arena/docker-compose.dev.yml up --build
```

The dev override disables `cloudflared` by default. To test the tunnel with the
local stack, append `--profile tunnel` and provide a valid tunnel token.

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
- `outbox` runs `python -m src.outbox_worker` from the Tatami backend image and pushes queued records to `EXTERNAL_API_URL/sync/upserts`
