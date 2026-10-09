# Sync Rewrite Status and Next Steps

The current wire contract and DTO reference are defined in `docs/SYNC_ARCHITECTURE.md`. This file is a roadmap, not a second contract.

## Current state

The original event-driven rewrite is substantially complete:

| Area | Status |
| --- | --- |
| One-time Arena-to-Tatami bootstrap snapshot | Implemented |
| Repeated inbound runtime sync blocked | Implemented |
| Tatami-to-Arena aggregate upserts | Implemented for `match.upsert` and `bracket.upsert` |
| `seq` downgraded to diagnostics | Implemented |
| Inbox deduplication by `event_id` | Implemented |
| Bracket-version conflict check | Implemented |
| Legacy `/sync/commands` runtime route | Removed; stale tests still reference it |
| Full outbox observability and recovery | Not implemented |
| Safe concurrent/leased worker | Not implemented |
| Automatic reconciliation | Not implemented |
| Python replacement for the Go worker | Proposed |

## Next milestone: make delivery semantics explicit

Before replacing the worker, settle and test these rules against the contract:

1. Classify failures as retryable transport failures or terminal application rejections.
2. Expose terminal failures (`skipped`/future `dead_letter`) to operators.
3. Define recovery for `version_conflict`, `aggregate_not_found`, and `apply_failed`.
4. Decide whether a rejected `event_id` remains permanently deduplicated or can be explicitly replayed.
5. Stop treating `last_applied_seq` as a successful-delivery barrier; it currently advances for rejected items.
6. Define a reconciliation command that creates a new event from current local aggregate state.
7. Validate that each aggregate belongs to the envelope's `tournament_id` before applying it.
8. Decide whether equal-version, different-content payloads are conflicts rather than valid overwrites.

## Next milestone: replace the Go worker with Python

The delivery worker should move into the Tatami backend codebase to remove duplicated models, configuration, and acknowledgement logic. It should still run as a dedicated process, not inside the FastAPI/Gunicorn web lifecycle.

Recommended shape:

- reuse `OutboxItem` and sync DTOs from the Python backend;
- use a dedicated CLI/module entry point in the Tatami backend image;
- claim work with `FOR UPDATE SKIP LOCKED` or an explicit lease;
- recover expired `processing` leases after worker crashes;
- add `next_attempt_at` and bounded exponential backoff;
- use explicit terminal status such as `dead_letter` instead of an invisible `skipped` state;
- process independent later items without head-of-line blocking;
- preserve `event_id` across transport retries;
- remove the Go image/service only after parallel contract verification.

## Contract hardening

The following should be addressed independently of worker language:

- Add contract tests using the current `/sync/upserts` DTOs; remove stale `/sync/commands` tests.
- Test `accepted + seq_gap` as successful application.
- Test `version_conflict` as a terminal rejected application.
- Test equal-version idempotent overwrite deliberately.
- Test batch requests even though the current producer sends one item.
- Test full `bracket.upsert` replacement and placement recalculation.
- Validate that athlete, bracket, match, and tournament IDs always use Arena identities on the wire.
- Decide whether bracket replacement should remain destructive or become an explicit diff/upsert operation.

## Later capabilities

Not implemented today:

- `tournament.upsert` for full outward recovery;
- `timetable.upsert`;
- operator-triggered resend/reconciliation UI;
- pending age, last successful delivery, and dead-letter metrics;
- versioned sync contract negotiation;
- safe multi-node conflict resolution.

## Invariants that must survive any rewrite

- Tatami remains operational without Arena connectivity.
- Local business mutation and outbox insertion are one DB transaction.
- Arena never receives Tatami-local entity IDs as aggregate identities.
- Older bracket versions cannot overwrite newer bracket state.
- Duplicate transport delivery is harmless.
- A transport acknowledgement is not confused with a business conflict.
- Sync transport stays outside `domain/champion_domain`.
