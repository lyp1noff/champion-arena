# Sync Architecture

Canonical sync model for `arena` <-> `control`.

This document replaces the old event-driven sync contract and the earlier edge/master sync plan.

## Goals

- `control` must remain fully operational during a tournament without network access.
- `arena` must stop being a live source of truth once the tournament is bootstrapped into `control`.
- Sync must be easy to reason about, debug, retry, and recover manually.
- Shared domain logic must stay reusable by both applications, but transport rules must not leak into the domain package.

## Source of Truth

### Before tournament start

- `arena` is the source of truth.
- `control` performs a one-time bootstrap import.

### During tournament runtime

- `control` is the source of truth.
- Incoming updates from `arena` are blocked.
- `control` sends state updates outward to `arena`.

### Recovery mode

- Operator may trigger a full tournament resend from `control` to `arena`.
- This is a repair tool, not a normal operating mode.

## Sync Pattern

The system uses two distinct flows.

### 1. Bootstrap Snapshot

Direction:
- `arena -> control`

Purpose:
- one-time import before local autonomous runtime

Transport shape:
- plain REST snapshot
- no event sequencing
- no inbox/outbox semantics

Suggested endpoint:
- `GET /tournaments/{id}/bootstrap-snapshot`

Payload includes:
- tournament metadata
- brackets
- bracket participants
- bracket matches
- timetable

After bootstrap:
- `control` marks the tournament as locally owned
- repeat imports are blocked unless an explicit operator reset happens before the tournament starts

### 2. Aggregate Upsert Sync

Direction:
- `control -> arena`

Purpose:
- send the latest full state of the changed aggregate

Suggested endpoint:
- `POST /sync/upserts`

Allowed aggregate types in the first version:
- `match.upsert`
- `bracket.upsert`
- `timetable.upsert` (optional if bracket/tournament payloads already cover the needed edits)
- `tournament.upsert` only for manual recovery / resend

## Aggregate Strategy

Do not sync tiny actions like:
- `match.started`
- `match.score_updated`
- `match.finished`
- `participant.moved`
- `participant.seeded`

Instead, sync the final state of the aggregate that changed.

### Match changes

When local runtime changes a match:
- send full `match` state

Example use cases:
- match started
- score changed
- match finished
- manual score correction

### Bracket changes

When local operator changes bracket structure:
- send full `bracket` state

Example use cases:
- participant removed
- participant moved
- reseeding
- bracket regeneration
- repechage structure rebuilt

If a participant move affects two brackets:
- send two `bracket.upsert` payloads

### Tournament resend

If local operator suspects missed updates:
- resend full tournament snapshot outward

This is the fallback repair path.

## Sequencing and Versions

### `seq`

`seq` is no longer a blocking correctness mechanism.

It may be kept only for:
- logging
- tracing
- debugging gaps

Missing sequence values must not block later payload application.

If `seq` gap is detected:
- record a warning
- continue processing newer payloads

### Aggregate version

Correctness is based on aggregate version, not global event order.

Rules:
- every mutable aggregate carries its own `version`
- `match.version` controls `match.upsert`
- `bracket.version` controls `bracket.upsert`
- `tournament.version` controls `tournament.upsert`

Application rule:
- accept payload if incoming version is newer than or equal to the stored version according to the chosen write policy

Recommended policy:
- reject older versions
- accept equal version only if payload is idempotent / same-state safe
- accept newer versions and overwrite aggregate state

## Failure Semantics

The sync model must tolerate:
- dropped packets
- retries
- duplicate sends
- out-of-order arrival

Because payloads are full aggregate states:
- a later `bracket.upsert` can heal a lost earlier `match.upsert`
- a full `tournament.upsert` can heal a lost earlier `bracket.upsert`

This is the main reason to prefer aggregate upserts over action events.

## Domain Boundary

Shared `domain` must own:
- bracket planning
- round classification
- repechage planning
- placements
- mutability rules
- future timetable planning rules

Shared `domain` must not own:
- sync envelopes
- `edge_id`
- `seq`
- HTTP DTOs
- outbox/inbox persistence semantics

Transport DTOs live in service layers only.

## Immediate Simplification Targets

The following legacy concepts are no longer part of the target design:

- blocking `out_of_order`
- master inbox sequencing as a correctness gate
- runtime event types for match state transitions
- `bracket.structure_rebuilt` as a special transport-only case
- dual live sync directions during tournament runtime

## Implementation Route

### Phase 1. Freeze the model

- add bootstrap-only rule to `control`
- stop treating `arena` as a live upstream during tournament runtime
- document `control` as the runtime source of truth

### Phase 2. Add clean bootstrap endpoint

- build one canonical tournament snapshot from `arena`
- import it into `control`
- remove any expectation of repeated destructive resync during runtime

### Phase 3. Replace event sync with aggregate upserts

- add `POST /sync/upserts` on `arena`
- make `control` outbox send full `match` / `bracket` / `tournament` payloads
- downgrade `seq` to diagnostics only

### Phase 4. Remove old sync machinery

- delete legacy event DTOs
- delete inbox/out_of_order correctness logic
- delete command-style sync routing

### Phase 5. Build local admin UI

- participant changes on `control`
- bracket rebuild/regenerate on `control`
- timetable editing on `control`
- outbox visibility and manual resend tools

## Practical Rule

If a change matters to tournament runtime, `control` applies it locally first and only then sends the resulting aggregate state to `arena`.
