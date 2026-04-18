import unittest

from champion_domain.use_cases import (
    FinishedMainMatch,
    plan_repechage_generation,
    should_attempt_repechage_generation_on_finish,
    should_generate_repechage,
    should_publish_structure_after_match_finish,
)


class RepechagePolicyTests(unittest.TestCase):
    def test_should_generate_repechage_positive(self) -> None:
        self.assertTrue(
            should_generate_repechage(
                bracket_type="single_elimination",
                main_rounds=3,
                has_repechage_matches=False,
                finalist_a_id=10,
                finalist_b_id=20,
            )
        )

    def test_should_generate_repechage_negative_cases(self) -> None:
        self.assertFalse(
            should_generate_repechage(
                bracket_type="round_robin",
                main_rounds=3,
                has_repechage_matches=False,
                finalist_a_id=10,
                finalist_b_id=20,
            )
        )
        self.assertFalse(
            should_generate_repechage(
                bracket_type="single_elimination",
                main_rounds=1,
                has_repechage_matches=False,
                finalist_a_id=10,
                finalist_b_id=20,
            )
        )
        self.assertFalse(
            should_generate_repechage(
                bracket_type="single_elimination",
                main_rounds=3,
                has_repechage_matches=True,
                finalist_a_id=10,
                finalist_b_id=20,
            )
        )

    def test_plan_repechage_generation(self) -> None:
        result = plan_repechage_generation(
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
        self.assertEqual(len(result.plans), 2)
        self.assertEqual(result.max_step_by_side["A"], 1)
        self.assertEqual(result.max_step_by_side["B"], 1)

    def test_finish_flow_policies(self) -> None:
        self.assertTrue(
            should_attempt_repechage_generation_on_finish(
                origin="local",
                stage="main",
            )
        )
        self.assertFalse(
            should_attempt_repechage_generation_on_finish(
                origin="sync",
                stage="main",
            )
        )
        self.assertFalse(
            should_attempt_repechage_generation_on_finish(
                origin="local",
                stage="repechage",
            )
        )

        self.assertTrue(
            should_publish_structure_after_match_finish(
                is_repechage_match=False,
                generated_repechage=True,
            )
        )
        self.assertFalse(
            should_publish_structure_after_match_finish(
                is_repechage_match=True,
                generated_repechage=True,
            )
        )


if __name__ == "__main__":
    unittest.main()
