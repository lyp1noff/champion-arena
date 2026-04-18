# Sync Rewrite Plan

Concrete implementation route for replacing the legacy sync model.

Canonical architecture is defined in:
- `docs/SYNC_ARCHITECTURE.md`

## Target State

Runtime rules:
- `arena -> control` only for one-time bootstrap before tournament runtime
- `control -> arena` for all runtime state propagation
- `control` is the source of truth during the tournament
- no repeated destructive pull sync during runtime
- `seq` is diagnostics only, never a blocking correctness gate
- aggregate versions decide payload applicability

Transport model:
- `bootstrap snapshot`
- `aggregate upserts`

Aggregate types for first implementation:
- `match.upsert`
- `bracket.upsert`
- `tournament.upsert` for manual recovery

## Phase 1. Freeze Incoming Runtime Sync

Goal:
- stop treating `arena` as a live upstream once `control` has bootstrapped a tournament

Work:
- restrict `tatami/backend/src/services/sync.py` to bootstrap/import responsibilities only
- remove or disable repeated runtime resync entry points
- add explicit local-ownership / sync-lock state on the `control` side
- update docs and admin UI messaging later to reflect bootstrap-only behavior

Done when:
- operator can bootstrap once
- operator cannot apply repeated runtime updates from `arena`

## Phase 2. Add Canonical Bootstrap Snapshot

Goal:
- replace ad hoc sync payloads with one clean tournament snapshot exported by `arena`

Work in `arena`:
- add a snapshot builder in service layer
- expose `GET /tournaments/{id}/bootstrap-snapshot`
- include tournament, brackets, bracket participants, matches, timetable

Work in `control`:
- import the snapshot into local persistence
- keep mapping code in service layer, not in `domain`

Done when:
- `control` can bootstrap tournament state from one canonical snapshot endpoint

## Phase 3. Replace Event Sync with Aggregate Upserts

Goal:
- stop sending tiny action events and send full aggregate state instead

Work in `control`:
- replace event payload builders in `tatami/backend/src/services/outbox.py`
- remove dependency on `tatami/backend/src/services/outbox_event_dto.py`
- produce payloads for full `match`, full `bracket`, optional full `tournament`

Work in `arena`:
- add `POST /sync/upserts`
- apply incoming upserts by aggregate type and aggregate version
- log `seq` gaps only as warnings
- do not block on out-of-order arrival

Done when:
- lost `match` updates can be healed by later `bracket.upsert`
- retries and duplicate sends are idempotent

## Phase 4. Remove Legacy Sync Machinery

Goal:
- delete the old event-driven path after the new one is live

Likely removals from `arena`:
- `arena/backend/src/services/sync.py` legacy command flow
- `arena/backend/src/services/sync_match_dto.py`
- `arena/backend/src/services/sync_structure_dto.py`
- old `/sync/commands` request/response DTOs in `arena/backend/src/schemas.py`
- inbox/state tables that only exist for blocking event sequencing

Likely removals from `control`:
- event-style outbox DTO construction
- runtime pull/update semantics from `arena`

Done when:
- no code path depends on `match.started`, `match.finished`, `bracket.structure_rebuilt`, or blocking `out_of_order`

## Phase 5. Clean Domain Surface

Goal:
- keep `domain` as pure shared business logic only

Keep in `domain`:
- bracket generation and planning
- repechage planning and runtime progression
- placements and bracket completion
- mutability rules
- future timetable planning rules

Move out of `domain` or remove if transport-only:
- `domain/champion_domain/use_cases/match_command.py`
- transport-specific snapshot/rebuild wrappers if they only exist for sync compatibility
- any DTO whose main purpose is network payload shape rather than pure business logic

Done when:
- `domain` contains deterministic input/output logic only
- sync envelopes live only in application service layers

## Phase 6. Build Local Admin UI On Top of the New Model

Goal:
- make local operator edits first-class and resilient

Scope:
- participant changes in brackets
- bracket regeneration / repechage rebuild
- timetable editing

Rule:
- local UI mutates local state
- local state produces aggregate upserts outward
- master acknowledgement must not be required for local continuity

## First Code Slice

Recommended first implementation slice:
1. freeze repeated inbound runtime sync in `control`
2. define bootstrap snapshot DTO and endpoint in `arena`
3. import snapshot in `control`
4. only then start replacing outbox events with aggregate upserts

Reason:
- it removes the most dangerous runtime ambiguity first
- it gives one stable data shape before changing outbound transport
