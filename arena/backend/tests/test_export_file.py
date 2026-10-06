from types import SimpleNamespace

from src.services.export_file import (
    _replace_placeholders,
    build_entry,
    build_round_robin_entry,
)


def _athlete(athlete_id: int, last_name: str) -> SimpleNamespace:
    return SimpleNamespace(
        id=athlete_id,
        last_name=last_name,
        first_name=f"First{athlete_id}",
        coach_links=[],
    )


def _bracket_match(
    round_number: int,
    position: int,
    athlete1: SimpleNamespace,
    athlete2: SimpleNamespace,
    score1: int | None = None,
    score2: int | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        round_number=round_number,
        position=position,
        match=SimpleNamespace(
            athlete1=athlete1,
            athlete2=athlete2,
            score_athlete1=score1,
            score_athlete2=score2,
        ),
    )


def test_elimination_filled_export_keeps_later_rounds_while_manual_does_not() -> None:
    athlete1 = _athlete(1, "One")
    athlete2 = _athlete(2, "Two")
    winner = _athlete(3, "Winner")
    finalist = _athlete(4, "Finalist")
    matches = [
        _bracket_match(1, 1, athlete1, athlete2),
        _bracket_match(2, 1, winner, finalist),
    ]
    bracket = SimpleNamespace(category=SimpleNamespace(name="U18"))

    filled = build_entry(matches, bracket, 0, 0, "10:00", "Cup", mode="filled")
    manual = build_entry(matches, bracket, 0, 0, "10:00", "Cup", mode="manual")

    assert filled["round1_position1_athlete1"].startswith("One First1")
    assert filled["round2_position1_athlete1"].startswith("Winner First3")
    assert manual["round1_position1_athlete1"].startswith("One First1")
    assert "round2_position1_athlete1" not in manual


def test_round_robin_filled_export_adds_mirrored_scores() -> None:
    athlete1 = _athlete(1, "One")
    athlete2 = _athlete(2, "Two")
    matches = [_bracket_match(1, 1, athlete1, athlete2, score1=3, score2=1)]

    filled = build_round_robin_entry(matches, "U18", "10:00", "Cup", mode="filled")
    manual = build_round_robin_entry(matches, "U18", "10:00", "Cup", mode="manual")

    assert filled["score_1_2"] == "3 : 1"
    assert filled["score_2_1"] == "1 : 3"
    assert "score_1_2" not in manual


def test_placeholders_are_replaced_without_requiring_spaces() -> None:
    svg = '<svg xmlns="http://www.w3.org/2000/svg"><text>[[score_1_2]]</text></svg>'

    rendered = _replace_placeholders(svg, {"score_1_2": "3 : 1"})

    assert rendered == '<svg xmlns="http://www.w3.org/2000/svg"><text>3 : 1</text></svg>'
