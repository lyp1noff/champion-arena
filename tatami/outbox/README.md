# Tatami Outbox Worker

This Go service is the current delivery process for Tatami's transactional outbox. The canonical HTTP contract, DTOs, version rules, and known limitations are documented in `../../docs/SYNC_ARCHITECTURE.md`.

The worker is expected to be replaced by a dedicated Python process in the Tatami backend codebase. Until that migration is complete, this README describes the running Go implementation.

## What it does

The Tatami Python backend writes a complete serialized HTTP request to `outbox_items` in the same database transaction as the local tournament change. This worker:

1. polls the shared PostgreSQL database;
2. claims the oldest `pending` or retryable `failed` row;
3. sends the stored method, endpoint, payload, and bearer token;
4. interprets `/sync/upserts` acknowledgements;
5. marks the row `success`, `failed`, or `skipped`.

It does not create sync DTOs, increment aggregate versions, or decide business conflicts. Those responsibilities belong to the Python producer and Arena receiver.

## Configuration

| Variable | Default | Actual use |
| --- | --- | --- |
| `POSTGRES_USER` | empty | PostgreSQL user. |
| `POSTGRES_PASSWORD` | empty | PostgreSQL password. |
| `POSTGRES_HOST` | `localhost` | PostgreSQL host. |
| `POSTGRES_PORT` | `5432` | PostgreSQL port. |
| `POSTGRES_DB` | empty | PostgreSQL database. |
| `EXTERNAL_API_TOKEN` | empty | Sent as `Authorization: Bearer ...`. |
| `PROCESSING_INTERVAL` | `1s` | Poll interval. |
| `HTTP_TIMEOUT` | `10s` | Per-request HTTP timeout. |
| `BATCH_SIZE` | `10` | Parsed and logged, but currently unused; processing is one row at a time. |
| `LOG_LEVEL` | `info` | `debug`, `info`, `warn`, or `error`. |

`EXTERNAL_API_URL` is parsed by the config package but delivery uses the endpoint already stored in each outbox row. The Python producer constructs that endpoint from its own `EXTERNAL_API_URL`.

## Expected table

The worker reads the SQLAlchemy-managed Tatami table:

```text
outbox_items
  id              integer primary key
  tournament_id   nullable local Tatami FK
  match_id        nullable local Tatami FK
  endpoint        string
  method          string
  payload         nullable serialized JSON
  status          pending | processing | failed | success | skipped
  retry_count     integer
  max_retries     integer
  error           nullable text
  created_at      timestamp
  updated_at      timestamp
```

Do not maintain a separate Go-owned migration/schema for this table.

## Acknowledgement behavior

For a 2xx `/sync/upserts` response:

- a non-empty `accepted` or `duplicates` list is success;
- `seq_gap` may accompany `accepted` and does not turn it into a failure;
- a conflict without an acknowledgement is non-retryable and becomes `skipped`;
- invalid or empty acknowledgement JSON is retryable.

Network failures, HTTP 408/429, and 5xx responses are retryable. Other HTTP failures are terminal.

On retryable failure, `retry_count` is incremented and the worker waits 10 seconds. Rows stop being selected once `retry_count` reaches their stored `max_retries` value.

## Running locally

From this directory:

```bash
go run ./cmd/outbox-worker
```

The normal development and production Compose files start this service with the Tatami backend and database.

## Current limitations

- Run only one worker replica: claiming has no locking lease or `SKIP LOCKED` protection.
- A process crash can strand a row in `processing`.
- The oldest retrying row blocks later rows until success or retry exhaustion.
- `BATCH_SIZE` does not affect processing.
- `skipped` is not included by the current Tatami `/outbox/status` endpoint.
- There is no automatic resend/reconciliation for terminal application conflicts.
- Cancellation is only wired to a background context; OS signal shutdown is not explicitly handled.

These are migration requirements for the planned Python worker, not guarantees of the current service.
