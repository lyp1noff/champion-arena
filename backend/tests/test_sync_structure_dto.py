from datetime import UTC, datetime
from uuid import uuid4

from src.services.sync_structure_dto import parse_structure_payload_dto


def test_parse_structure_payload_dto_derives_main_labels() -> None:
    payload = {
        "participants": [{"athlete_id": 1, "seed": 1}, {"athlete_id": 2, "seed": 2}],
        "matches": [
            {
                "id": str(uuid4()),
                "round_number": 1,
                "position": 1,
                "next_slot": None,
                "round_type": "round",
                "stage": "repechage",
                "status": "not_started",
                "athlete1_id": 1,
                "athlete2_id": 2,
                "winner_id": None,
                "score_athlete1": None,
                "score_athlete2": None,
                "repechage_side": "A",
                "repechage_step": 1,
                "started_at": None,
                "ended_at": None,
            }
        ],
        "state": "locked",
    }

    participants, matches, state, status = parse_structure_payload_dto(payload)
    assert len(participants) == 2
    assert len(matches) == 1
    assert matches[0].round_type == "final"
    assert matches[0].stage == "main"
    assert matches[0].repechage_side is None
    assert matches[0].repechage_step is None
    assert state == "locked"
    assert status is None


def test_parse_structure_payload_dto_derives_repechage_labels() -> None:
    payload = {
        "participants": [{"athlete_id": i, "seed": i} for i in range(1, 7)],
        "matches": [
            {
                "id": str(uuid4()),
                "round_number": 4,
                "position": 1,
                "next_slot": 1,
                "round_type": "final",
                "stage": "main",
                "status": "not_started",
                "athlete1_id": 1,
                "athlete2_id": 2,
                "winner_id": None,
                "score_athlete1": None,
                "score_athlete2": None,
                "repechage_side": None,
                "repechage_step": None,
                "started_at": datetime.now(UTC).isoformat(),
                "ended_at": None,
            }
        ],
        "state": None,
    }

    _, matches, _, status = parse_structure_payload_dto(payload)
    assert len(matches) == 1
    assert matches[0].stage == "repechage"
    assert matches[0].round_type == "round"
    assert matches[0].repechage_side == "A"
    assert matches[0].repechage_step == 1
    assert status is None
