## champion-domain

Shared business logic for Champion services (`champion-arena`, `champion-tatami`).

This package contains pure domain rules/use-cases and should not depend on:
- FastAPI
- SQLAlchemy
- Pydantic transport models
- HTTP/JSON transport concerns

## What is inside

- bracket generation helpers
- bracket/match policies
- match progression
- repechage runtime planning
- structure snapshot/rebuild typed DTOs (domain-level)

## Usage

```python
from champion_domain import compute_main_rounds, classify_bracket_match

main_rounds = compute_main_rounds(6)
label = classify_bracket_match(round_number=3, position=1, main_rounds=main_rounds)
```

## Versioning

Semver:
- patch: internal fixes, no public API break
- minor: additive API changes
- major: breaking API/contract changes
