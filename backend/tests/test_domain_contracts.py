from champion_domain import (
    FinishedMainMatch,
    compute_progression_action,
    decide_bracket_completion,
    plan_repechage_generation,
    should_attempt_repechage_generation_on_finish,
    should_finish_tournament,
    should_generate_repechage,
    should_publish_structure_after_match_finish,
)


def test_progression_contract_main_and_repechage() -> None:
    main_action = compute_progression_action(
        stage="main",
        current_round_number=1,
        current_position=2,
        explicit_next_slot=None,
        allow_implicit_main_slot=True,
    )
    assert main_action is not None
    assert main_action.kind == "main"
    assert main_action.main_round_number == 2
    assert main_action.main_position == 1
    assert main_action.slot == 2

    rep_action = compute_progression_action(
        stage="repechage",
        current_round_number=4,
        current_position=1,
        explicit_next_slot=None,
        repechage_side="A",
        repechage_step=1,
        main_rounds=3,
    )
    assert rep_action is not None
    assert rep_action.kind == "repechage"
    assert rep_action.repechage_side == "A"
    assert rep_action.repechage_step == 2
    assert rep_action.repechage_round_number == 5
    assert rep_action.repechage_position == 1


def test_repechage_policy_contract() -> None:
    assert should_generate_repechage(
        bracket_type="single_elimination",
        main_rounds=3,
        has_repechage_matches=False,
        finalist_a_id=10,
        finalist_b_id=20,
    )
    assert not should_generate_repechage(
        bracket_type="single_elimination",
        main_rounds=1,
        has_repechage_matches=False,
        finalist_a_id=10,
        finalist_b_id=20,
    )

    generation = plan_repechage_generation(
        finalist_a_id=10,
        finalist_b_id=20,
        finished_main_matches=[
            FinishedMainMatch(round_number=1, winner_id=10, athlete1_id=10, athlete2_id=11),
            FinishedMainMatch(round_number=2, winner_id=10, athlete1_id=10, athlete2_id=12),
            FinishedMainMatch(round_number=1, winner_id=20, athlete1_id=20, athlete2_id=21),
            FinishedMainMatch(round_number=2, winner_id=20, athlete1_id=20, athlete2_id=22),
        ],
        base_round=4,
    )
    assert len(generation.plans) == 2
    assert generation.max_step_by_side == {"A": 1, "B": 1}
    assert should_attempt_repechage_generation_on_finish(origin="local", stage="main")
    assert not should_attempt_repechage_generation_on_finish(origin="sync", stage="main")
    assert should_publish_structure_after_match_finish(is_repechage_match=False, generated_repechage=True)
    assert not should_publish_structure_after_match_finish(is_repechage_match=True, generated_repechage=True)
    completion = decide_bracket_completion(total_matches=3, finished_matches=3, current_bracket_status="started")
    assert completion.should_finish_bracket
    assert should_finish_tournament(0)
