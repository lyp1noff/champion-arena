# Sync Contract

Scope: edge (`champion-tatami-control`) -> master (`champion-arena`) tournament sync.

## Transport Envelope

All sync commands use one envelope:

```json
{
  "edge_id": "tatami-node-02",
  "events": [
    {
      "event_id": "uuid",
      "seq": 123,
      "event_type": "match.started",
      "aggregate_type": "match",
      "aggregate_id": "aggregate-id",
      "aggregate_version": 42,
      "occurred_at": "2026-02-03T21:49:57.216737+00:00",
      "payload": {}
    }
  ]
}
```

## Sequencing Rules

- `seq` is strictly increasing per `edge_id`.
- Master accepts only `seq == last_applied_seq + 1`.
- Otherwise conflict reason is `out_of_order`.
- Duplicate `(edge_id, seq)` is treated as duplicate (idempotent no-op).

## Versioning Rules

- `aggregate_version` is optimistic version of target aggregate.
- For `match.*` events master expects `current_bracket_version + 1`.
- For `bracket.structure_rebuilt` master expects `bracket.version + 1`.
- Mismatch -> `version_conflict`.

## Event Types

### Runtime Events (`aggregate_type=match`)

- `match.started`
- `match.score_updated`
- `match.finished`
- `match.status_updated`

Runtime events mutate existing matches only.

### Structural Event (`aggregate_type=bracket`)

- `bracket.structure_rebuilt`

Structural event is used for bracket shape/state replacement:
- participants
- matches graph and match states
- bracket `state`/`status`

## Structural vs Runtime Ownership

- Structural changes are published with `bracket.structure_rebuilt` only.
- Runtime updates use `match.*` only.
- Do **not** publish `bracket.structure_rebuilt` on every score/start/finish.

## Origin Rules on Master

`finish_match(origin=...)`:
- `origin="local"`: local business flow may generate repechage/structural side effects.
- `origin="sync"`: no local structural generation, apply only incoming command.

## Domain Normalization

Incoming/outgoing structure match labels are normalized by shared domain:
- `compute_main_rounds`
- `classify_bracket_match`
- `build_structure_match`

Do not trust incoming raw `round_type`/`stage`/`repechage_*`; normalize through domain builders.

## Required Invariants

- Final main match has `round_type="final"`.
- Repechage matches have `stage="repechage"` and `round_type="round"`.
- `next_slot` reflects real graph edges (`null` for terminal nodes).
- `match.*` references existing matches on master.

## Failure Semantics

Master returns:
- `accepted`: applied seq values
- `duplicates`: already seen seq values
- `conflicts`: per-event conflict records (`reason`, optional expected/received versions)
- `last_applied_seq`

This contract is normative for new sync logic. Legacy compatibility is out of scope.
