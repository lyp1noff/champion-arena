# Sync Contract and Architecture

This is the canonical description of the sync contract currently implemented between `arena` and `tatami`.
It describes running code, not the deprecated `/sync/commands` design. Planned changes are explicitly marked as such.

## Short version

There are two one-way flows:

1. Before local work starts, Tatami downloads a full tournament bootstrap snapshot from Arena.
2. During the tournament, Tatami changes its local database first and writes a full aggregate snapshot to its local outbox in the same transaction.
3. The outbox worker sends that stored envelope to `POST /sync/upserts` on Arena.
4. Arena deduplicates by `event_id`, checks the incoming bracket version, applies the snapshot, stores the inbox result, and returns an acknowledgement.
5. Network failures are retried. A rejected payload is not automatically merged; it needs operator-visible recovery or rebootstrap/reconciliation.

The runtime rule is therefore:

> Tatami is the source of truth during tournament operation. Arena is an eventually consistent projection of Tatami state.

The transport sends state, not actions. There are no `match.started` or `match.finished` messages in the current contract; both become `match.upsert` with the complete current match state.

## Terminology and ownership

- **Arena**: central application and source of truth before bootstrap.
- **Tatami**: local, offline-capable application; historically called `control` or `edge` in older documents.
- **Aggregate**: the unit whose state and version are synchronized. Currently this is effectively the bracket, even when the payload type is `match.upsert`.
- **Outbox item**: a local Tatami DB row containing an immutable HTTP request and its serialized sync envelope.
- **Inbox event**: Arena's record that an `event_id` was seen and whether it was applied.

Shared business rules live in `domain/champion_domain`. HTTP envelopes, persistence, retry rules, `edge_id`, and `seq` are application-layer concerns and must not be moved into the domain package.

## Source of truth by phase

### Before bootstrap

Arena owns tournament setup, athletes, brackets, matches, and timetable data.

### After bootstrap and during runtime

Tatami owns operational state. Match control and permitted bracket edits are committed locally without waiting for Arena.

Repeated inbound sync is blocked when a local tournament copy already exists. `POST /tournaments/{id}/rebootstrap` is an explicit destructive recovery operation: it removes the local copy and imports it again from Arena. It is not a routine refresh mechanism and can discard local state and queued work.

## Flow 1: bootstrap snapshot

Direction: `Arena -> Tatami`.

Arena endpoint:

```text
GET /tournaments/{tournament_id}/bootstrap-snapshot
Authorization: Bearer <service token>
```

Tatami starts this flow through:

```text
POST /tournaments/{tournament_id}/sync
```

Tatami then requests the Arena endpoint above using `EXTERNAL_API_TOKEN`. The Arena response contains:

- `tournament`: tournament metadata;
- `brackets`: brackets with participants;
- `bracket_matches`: brackets with complete match structures;
- `timetable_entries`: scheduling data.

Tatami stores Arena primary IDs as `external_id`. Local integer IDs remain implementation details and must never be sent to Arena as aggregate or athlete identities.

Bootstrap has no `seq`, inbox, or outbox semantics. It is a direct authenticated snapshot import.

## Flow 2: aggregate upsert

Direction: `Tatami -> Arena`.

Arena endpoint:

```text
POST /sync/upserts
Authorization: Bearer <service token>
Content-Type: application/json
```

Supported item types:

- `match.upsert`;
- `bracket.upsert`.

Other values return an `unsupported_upsert_type` conflict. `tournament.upsert` and `timetable.upsert` are not implemented.

Although the endpoint accepts an `items` array, the current Tatami producer creates one outbox row and one item per request.

### End-to-end write path

1. A Tatami service mutates a match or bracket inside a DB transaction.
2. It increments `Bracket.version` via `_touch_bracket`.
3. It serializes the complete current match or bracket state.
4. It inserts an `outbox_items` row before committing the same transaction.
5. The worker claims the row and sends its stored request.
6. Arena validates and applies the item in its own transaction.
7. Arena records the `event_id` in `sync_inbox_events` and advances the diagnostic watermark for `(edge_id, tournament_id)`.
8. The worker maps the acknowledgement to a terminal or retryable local status.

For match finish/correction, Tatami may enqueue a `match.upsert` followed by a newer `bracket.upsert`. The bracket snapshot is the healing/full-structure message and may supersede the narrower match message.

## Request envelope DTO

Current wire shape:

```json
{
  "edge_id": "tatami-node-01",
  "tournament_id": 6,
  "items": [
    {
      "event_id": "3dc9c8cb-4621-4ee2-a7fd-52d84ce0f181",
      "seq": 42,
      "type": "match.upsert",
      "aggregate_id": "f433cb15-6244-4115-84f0-dc0c2adb005f",
      "aggregate_version": 8,
      "occurred_at": "2026-10-09T12:00:00Z",
      "payload": {}
    }
  ]
}
```

### Envelope fields

| Field | Type | Meaning |
| --- | --- | --- |
| `edge_id` | non-empty string, max 100 | Stable ID of a physical Tatami installation. It must be unique per independently operating node. |
| `tournament_id` | positive integer | Arena tournament ID, not Tatami's local tournament PK. |
| `items` | array | Upserts. The API can accept several, but the current producer sends one. |

### Item fields

| Field | Type | Meaning |
| --- | --- | --- |
| `event_id` | UUID | Idempotency key generated once when the outbox row is created. Retries reuse it. |
| `seq` | positive integer | Currently the Tatami `outbox_items.id`. It is diagnostic, not an ordering gate. |
| `type` | string | `match.upsert` or `bracket.upsert`. |
| `aggregate_id` | string | Arena match UUID for a match item; decimal Arena bracket ID for a bracket item. |
| `aggregate_version` | positive integer | The enclosing bracket version for both supported item types. |
| `occurred_at` | ISO-8601 datetime | Time when Tatami created the outbox entry. |
| `payload` | object | Type-specific full-state payload. |

### Identity rules

| Value | Wire identity |
| --- | --- |
| Tournament | Arena integer ID (`Tournament.external_id` on Tatami) |
| Bracket aggregate | Arena integer ID serialized as a string (`Bracket.external_id`) |
| Match aggregate | Arena UUID serialized as a string (`Match.external_id`) |
| Athlete references | Arena integer athlete IDs (`Athlete.external_id`) |
| `seq` | Tatami local outbox row ID; never an entity ID |

## `match.upsert` payload DTO

```json
{
  "athlete1_id": 101,
  "athlete2_id": 202,
  "winner_id": 101,
  "round_type": "semifinal",
  "stage": "main",
  "repechage_side": null,
  "repechage_step": null,
  "score_athlete1": 3,
  "score_athlete2": 1,
  "status": "finished",
  "started_at": "2026-10-09T11:55:00Z",
  "ended_at": "2026-10-09T11:58:12Z"
}
```

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `athlete1_id`, `athlete2_id` | integer or null | no | Arena athlete IDs; referenced athletes must already exist. |
| `winner_id` | integer or null | no | Arena athlete ID. |
| `round_type` | string or null | no | Display/domain classification. |
| `stage` | string | no | Defaults to `main`; current values are `main` and `repechage`. |
| `repechage_side` | string or null | no | Usually `A` or `B`. |
| `repechage_step` | integer or null | no | Step within a repechage path. |
| `score_athlete1`, `score_athlete2` | integer or null | no | Current complete scores. |
| `status` | string | yes | Current match status: normally `not_started`, `started`, or `finished`. |
| `started_at`, `ended_at` | datetime or null | no | UTC timestamps when known. |

Arena requires the match UUID to exist and belong to a bracket. Applying the payload updates the match, advances the bracket version to `max(current, incoming)`, derives bracket runtime state, recomputes placements, and publishes a websocket refresh after commit.

## `bracket.upsert` payload DTO

```json
{
  "type": "single_elimination",
  "group_id": 1,
  "status": "started",
  "state": "running",
  "participants": [
    { "athlete_id": 101, "seed": 1 },
    { "athlete_id": 202, "seed": 2 }
  ],
  "matches": [
    {
      "id": "f433cb15-6244-4115-84f0-dc0c2adb005f",
      "round_number": 1,
      "position": 1,
      "next_slot": null,
      "round_type": "final",
      "stage": "main",
      "repechage_side": null,
      "repechage_step": null,
      "status": "finished",
      "athlete1_id": 101,
      "athlete2_id": 202,
      "winner_id": 101,
      "score_athlete1": 3,
      "score_athlete2": 1,
      "started_at": "2026-10-09T11:55:00Z",
      "ended_at": "2026-10-09T11:58:12Z"
    }
  ]
}
```

### Bracket fields

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `type` | string | yes | Current bracket type, such as `single_elimination` or `round_robin`. |
| `group_id` | integer | no | Defaults to `1`. |
| `status` | string or null | no | Bracket status. |
| `state` | string or null | no | Structural lifecycle: `draft`, `locked`, `running`, or `finished`. |
| `participants` | array | yes | Complete participant snapshot. `seed` must be positive. |
| `matches` | array | yes | Complete match-structure snapshot. |

Each match structure has a UUID `id`, positive `round_number` and `position`, optional `next_slot`, full match state, and Arena athlete IDs.

The table describes the Tatami producer DTO. Arena's current parser is more permissive: it validates `participants`, `matches`, `status`, and `state`, while reading `type` and `group_id` directly with fallbacks to stored values. This asymmetry should be removed when the contract DTOs are unified.

`bracket.upsert` is replacement semantics, not a patch: Arena deletes the bracket's existing participants and matches and recreates them from the payload, then recomputes placements. Missing rows are therefore deletions.

Arena currently canonicalizes structural match labels (`round_type`, `stage`, `repechage_side`, and `repechage_step`) from `round_number`, `position`, and participant count through shared domain logic. Producers send those fields for a complete snapshot, but must not rely on arbitrary values surviving application.

## Version semantics

There is currently no independent `Match.version`. `Bracket.version` is the concurrency boundary for both match and bracket items.

Tatami increments the bracket version for:

- match start;
- score update;
- match finish or result correction;
- participant/seed/structure changes;
- bracket regeneration.

Arena applies this policy:

```text
incoming_version < stored_bracket_version  -> reject: version_conflict
incoming_version = stored_bracket_version  -> accept: idempotent/equal-version overwrite
incoming_version > stored_bracket_version  -> accept and advance version
```

Because equal versions are accepted, `event_id` remains the retry/deduplication key while the version prevents older state from overwriting newer state.

## Sequence and deduplication semantics

`seq` is deliberately non-blocking. Arena compares it with `last_applied_seq + 1`; a mismatch adds a `seq_gap` diagnostic but does not stop application.

This matters because:

- `seq` comes from a DB-wide outbox ID;
- Arena tracks its watermark per `(edge_id, tournament_id)`;
- events for different tournaments can legitimately make a tournament-specific sequence appear to have gaps.

Deduplication is by globally unique `event_id`, not by `seq`. Arena's inbox permits repeated sequence values and stores one row per event UUID.

`last_applied_seq` is a diagnostic high-water mark. It advances even when an item is rejected. It must not be interpreted as “all events up to this value were successfully applied.”

## Response DTO and acknowledgement rules

Example:

```json
{
  "accepted": [42],
  "duplicates": [],
  "conflicts": [
    { "seq": 42, "reason": "seq_gap", "expected_version": null, "received_version": null }
  ],
  "last_applied_seq": 42
}
```

| Field | Meaning |
| --- | --- |
| `accepted` | Sequence numbers whose payloads were applied. |
| `duplicates` | Sequence numbers whose `event_id` already existed; payload is not applied again. |
| `conflicts` | Diagnostics and rejected applications. A `seq_gap` may coexist with `accepted`. |
| `last_applied_seq` | Maximum diagnostic sequence observed for this edge and tournament. |

Known conflict reasons:

- `seq_gap`: diagnostic only; the item may still appear in `accepted`;
- `invalid_aggregate_id`;
- `aggregate_not_found`;
- `invalid_payload`;
- `unsupported_upsert_type`;
- `version_conflict`, with expected and received versions;
- `apply_failed`, for an unexpected server-side application failure.

Worker acknowledgement rule:

1. If the current item is present in `accepted` or `duplicates`, delivery succeeds even if `seq_gap` is also present.
2. If neither list acknowledges the item and `conflicts` is non-empty, delivery is a non-retryable rejected item.
3. Invalid/empty sync JSON, network errors, HTTP 408/429, and 5xx responses are retryable.

Arena records rejected `event_id` values in the inbox. Re-sending the same envelope will therefore be a duplicate, not a fresh application attempt. Recovery must create corrected state as a new outbox item/event or run an explicit reconciliation procedure.

## Persistence DTOs

### Tatami `outbox_items`

| Column | Purpose |
| --- | --- |
| `id` | Local serial ID and current `seq` source. |
| `tournament_id` | Tatami local tournament FK. |
| `match_id` | Optional Tatami local match FK. |
| `endpoint`, `method`, `payload` | Immutable HTTP request to send. |
| `status` | `pending`, `processing`, `failed`, `success`, or `skipped`. |
| `retry_count`, `max_retries` | Retry accounting. New entries currently use `max_retries=30`. |
| `error` | Last delivery/rejection message. |
| `created_at`, `updated_at` | Queue ordering and diagnostics. |

The payload stores the Arena tournament ID; the FK stores Tatami's local tournament ID. Mixing these IDs is a contract bug.

### Arena `sync_inbox_events`

| Column | Purpose |
| --- | --- |
| `event_id` | Primary idempotency key. |
| `edge_id`, `tournament_id`, `seq` | Origin and diagnostics. |
| `applied` | Whether aggregate application succeeded. |
| `error` | Conflict reason when not applied. |
| `received_at` | Receipt timestamp. |

### Arena `sync_edge_state`

One row per `(edge_id, tournament_id)` stores `last_applied_seq` and `updated_at`.

Status endpoint:

```text
GET /sync/status/{edge_id}?tournament_id={arena_tournament_id}
Authorization: Bearer <service token>
```

The response contains `edge_id`, `tournament_id`, `last_applied_seq`, and `server_time`. It is diagnostic only; it is not currently a safe sync barrier.

## Current worker behavior

The current delivery process is the separate Go service in `tatami/outbox`:

- polls at `PROCESSING_INTERVAL`;
- claims the oldest `pending` or retryable `failed` row;
- sends one row at a time (`BATCH_SIZE` is configured but currently unused);
- marks acknowledged items `success`;
- marks retryable failures `failed`, increments `retry_count`, then waits 10 seconds;
- marks non-retryable sync conflicts `skipped` and continues;
- stops selecting a failed row after `retry_count == max_retries`.

Current operational limitations:

- only one worker instance is safe; claiming has no `FOR UPDATE SKIP LOCKED` lease;
- a crash after claim can leave a row in `processing` indefinitely;
- retrying the oldest failed item causes head-of-line blocking until it succeeds or exhausts retries;
- `skipped` is not exposed by the current `/outbox/status` endpoint;
- there is no automatic reconciliation for version conflicts;
- `last_applied_seq` cannot prove that all earlier items were applied;
- worker metrics and manual resend/dead-letter tooling are incomplete.

Current correctness gaps to resolve before treating sync as hardened:

- Arena does not verify that an item's actual aggregate belongs to the envelope's `tournament_id`; an authenticated malformed request can update one tournament while recording inbox/watermark state under another.
- A rejected item is stored in the inbox by `event_id`; retrying the same event is returned as `duplicate` even though it was never applied.
- Equal-version payloads are accepted without comparing content, so two independently writing Tatami nodes can overwrite each other at the same version.
- An unexpected `apply_failed` is terminal from the current protocol's point of view, even when its root cause could be transient.
- Tatami's status endpoint omits `processing` and `skipped`, so its counters may not add up to `total`.

## Planned simplification

The Go worker is a replaceable transport implementation, not part of the wire contract. The preferred next design is a Python worker using the Tatami backend's SQLAlchemy model and DTOs, run as a separate process from the web server.

Moving it into Python must preserve these boundaries:

- create business state and the outbox row atomically;
- do not run the polling loop once per Gunicorn web worker;
- claim rows with a lease/`SKIP LOCKED` strategy;
- distinguish retryable delivery from terminal rejection/dead letter;
- expose terminal failures to operators;
- keep `event_id` stable for transport retries;
- create a new event only after producing corrected aggregate state;
- keep the HTTP contract in this document unchanged unless it is versioned deliberately.

## Code map

- Tatami envelope/payload DTOs: `tatami/backend/src/services/outbox_upsert_dto.py`
- Tatami outbox construction: `tatami/backend/src/services/outbox.py`
- Tatami aggregate version changes: `tatami/backend/src/services/matches.py`, `tatami/backend/src/services/brackets.py`
- Current worker: `tatami/outbox/internal`
- Arena HTTP DTOs: `arena/backend/src/schemas.py`
- Arena routes: `arena/backend/src/routers/sync.py`
- Arena application/version/inbox logic: `arena/backend/src/services/sync.py`
- Arena bracket snapshot parser: `arena/backend/src/services/bracket_upsert_dto.py`
- Bootstrap exporter: `arena/backend/src/services/tournaments.py`
- Bootstrap importer: `tatami/backend/src/services/sync.py`
- Shared structural normalization: `domain/champion_domain`

## Deprecated material

`docs/archive/EDGE_MASTER_SYNC_PLAN.deprecated.md` documents the removed command/event proposal and `/sync/commands`. It is historical context only and must not be used to implement clients.
