# Domain Boundaries

Canonical ownership rules for the monorepo.

This document replaces the older per-app boundary notes.

## Shared Domain

Shared package:
- `domain/champion_domain`

Owns pure business logic only:
- bracket generation
- round-robin scheduling
- seeded participant planning
- repechage planning
- match progression inside a bracket
- bracket completion and placements
- round labels and bracket classification
- bracket structural mutability rules
- future timetable planning rules

Characteristics:
- deterministic input/output
- no database access
- no network access
- no framework coupling
- reusable by both `arena` and `control`

## Service Layers

Service layers:
- `arena/backend/src/services`
- `tatami/backend/src/services`

Own:
- ORM loading and persistence
- transaction boundaries
- mapping DB rows to domain inputs
- mapping domain outputs back to stored state
- HTTP request/response DTOs
- broadcast / websocket side effects
- outbox delivery
- bootstrap import/export

Must not:
- reimplement bracket or repechage rules already present in `domain`
- encode transport concerns into `domain`

## Sync Ownership

Sync contracts belong to application services, not to `champion_domain`.

Application sync owns:
- bootstrap snapshot DTOs
- aggregate upsert DTOs
- outbox storage
- retry policy
- sync diagnostics

`champion_domain` must not own:
- `edge_id`
- `seq`
- envelopes
- transport event names
- inbox/outbox semantics

## Domain DTOs vs Transport DTOs

Allowed in domain:
- small dataclasses needed to represent pure domain inputs/outputs

Not allowed in domain:
- transport wrappers designed only for HTTP or queue payloads
- DTOs whose main purpose is compatibility with sync protocols

If a type exists only because of network transport, it belongs in backend service code.

## Routing Rule

When deciding where logic belongs:

- if it needs DB/session/HTTP/framework context, keep it in the service layer
- if it can be tested as pure computation, move it to `domain`

## Sync-Specific Implication

For the new sync model:
- aggregate payload assembly belongs to `arena` / `control`
- aggregate payload application belongs to `arena`
- bracket planning, repechage generation, placements, timetable planning belong to `domain`
