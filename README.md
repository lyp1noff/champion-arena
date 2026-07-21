# 🥋 Champion Arena

A monorepo for a full-stack **Karate Tournament Management System** built for real-world use.  
The platform covers the complete tournament lifecycle — from online registration to live match control on-site.

---

## 📦 Repository Structure

| Directory             | Description                                                                |
| --------------------- | -------------------------------------------------------------------------- |
| [`arena/`](./arena)   | Online tournament platform — registration, brackets, scheduling, results   |
| [`tatami/`](./tatami) | Local match control — referee dashboards, live scoring, offline-first sync |
| [`domain/`](./domain) | Shared Python domain library used by both backends                         |
| [`docs/`](./docs)     | Architecture docs, sync design, deployment guides                          |

---

## 🏗 Architecture

**Arena** runs in the cloud and handles the full tournament lifecycle.  
**Tatami** runs locally on-site and syncs results back to Arena via an outbox-based mechanism — ensuring match data is captured reliably even without a stable internet connection.

```
┌─────────────────────┐              ┌──────────────────────────┐
│    Arena (Cloud)    │              │   Tatami                 │
│                     │<── sync ─────│                          │
│  Next.js            │              │  Next.js                 │
│  FastAPI            │              │  FastAPI                 │
│  PostgreSQL         │              │  Go sync worker          │
└─────────────────────┘              │  PostgreSQL              │
                                     └──────────────────────────┘
```

---

## 🚀 Features

### Arena — Online Platform

- Athlete self-registration and coach management
- Tournament creation with configurable categories (age, weight, gender)
- Automated bracket generation
- Match scheduling and referee assignment
- Live result updates and automated rankings
- Export and print support for brackets and schedules

### Tatami — On-site Match Control

- Referee dashboard with digital scorekeeping
- Offline-first design — results stored locally, synced to Arena
- Outbox pattern for reliable event delivery
- Built for low-latency real-time match control at live events

---

## 🛠 Tech Stack

| Component      | Arena                                | Tatami                               |
| -------------- | ------------------------------------ | ------------------------------------ |
| **Frontend**   | Next.js (React)                      | Next.js (React)                      |
| **Backend**    | FastAPI (Python)                     | FastAPI (Python) + Go worker         |
| **Database**   | PostgreSQL + SQLAlchemy              | PostgreSQL                           |
| **Auth**       | OAuth2 / JWT                         | —                                    |
| **Sync**       | —                                    | Outbox pattern                       |
| **Deployment** | Docker, Nginx                        | Docker, Nginx                        |
| **Shared**     | [`domain/`](./domain) Python package | [`domain/`](./domain) Python package |

---

## 🐍 Python workspace

The Python services and the shared domain library are managed as one `uv` workspace.
The repository uses Python 3.12, a single root `uv.lock`, and one shared `.venv`.

```bash
uv sync --all-packages --all-groups
```

Run a command for a specific backend from the repository root with `--package`:

```bash
uv run --package champion pytest
uv run --package champion-tatami pytest
```

The existing `make -C arena back-*`, `make -C tatami back-*`, and `make -C domain lint`
commands use the same workspace environment.

---

## 📚 Documentation

- [Deployment & Environment Setup](./docs/DEPLOYMENT_AND_ENV.md)
- [Domain Boundaries](./docs/DOMAIN_BOUNDARIES.md)
- [Sync Architecture](./docs/SYNC_ARCHITECTURE.md)
