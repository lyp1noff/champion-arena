# Domain Boundaries

This document defines strict ownership between shared `champion_domain` and service layers (`champion-arena`, `champion-tatami-control`).

## Shared Domain (`champion_domain`)

Owns:
- bracket planning (`single_elimination`, `round_robin`, regeneration planner)
- progression rules (main/repechage next target/action)
- repechage policy and generation plan
- placement rules (1/2/3)
- pure typed inputs/outputs (dataclasses)

Does not own:
- HTTP transport
- ORM/SQLAlchemy models and persistence
- outbox/inbox storage
- framework concerns (FastAPI, Pydantic request/response models)

## Service Layer (`backend/src/services`, `_edge/backend/src/services`)

Owns:
- loading/storing ORM entities
- transaction boundaries
- mapping ORM -> domain input and domain output -> ORM updates
- side-effects (outbox, broadcasts, API responses)

Must not:
- reimplement domain rules already present in `champion_domain`
- parse transport payloads inside domain code

## Sync / Transport

Owns:
- envelope/payload DTO validation
- JSON serialization/deserialization
- compatibility around API contracts

Must not:
- encode business rules already in shared domain

## Practical Rule

If logic can be validated with deterministic input/output and requires no database/network/framework context, it belongs in `champion_domain`.
