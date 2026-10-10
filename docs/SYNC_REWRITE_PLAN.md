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
| Legacy `/sync/commands` runtime route | Removed |
| Full outbox observability and recovery | Implemented for current upsert types |
| Safe concurrent/leased worker | Implemented |
| Operator-triggered reconciliation | Implemented for current upsert types |
| Python replacement for the Go worker | Implemented |

## Delivery semantics

The worker now implements these rules:

1. Classify failures as retryable transport failures or terminal application rejections.
2. Expose terminal failures as `dead_letter` records to operators.
3. Recover terminal failures by creating a new event from current local aggregate state.
4. Keep a rejected `event_id` permanently deduplicated and never use raw resend as reconciliation.
5. Stop treating `last_applied_seq` as a successful-delivery barrier; it currently advances for rejected items.
6. Provide a reconciliation command that creates a new event from current local aggregate state.
7. Validate that each aggregate belongs to the envelope's `tournament_id` before applying it.
8. Decide whether equal-version, different-content payloads are conflicts rather than valid overwrites.

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
