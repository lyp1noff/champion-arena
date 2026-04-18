import unittest

from champion_domain.use_cases import (
    SeededParticipant,
    plan_round_robin_bracket,
    plan_single_elimination,
    plan_single_elimination_bracket,
    resolve_bye_advancements,
)


class BracketRegenerationTests(unittest.TestCase):
    def test_plan_round_robin_bracket_even(self) -> None:
        planned = plan_round_robin_bracket(
            [
                SeededParticipant(seed=1, athlete_id=101),
                SeededParticipant(seed=2, athlete_id=102),
                SeededParticipant(seed=3, athlete_id=103),
                SeededParticipant(seed=4, athlete_id=104),
            ]
        )
        self.assertEqual(len(planned), 6)
        self.assertEqual(planned[0].position, 1)
        self.assertEqual(planned[-1].position, 6)
        self.assertEqual(planned[0].round_number, 1)
        self.assertEqual(planned[0].round_type, "group")

    def test_plan_round_robin_bracket_odd_skips_dummy_pairs(self) -> None:
        planned = plan_round_robin_bracket(
            [
                SeededParticipant(seed=1, athlete_id=101),
                SeededParticipant(seed=2, athlete_id=102),
                SeededParticipant(seed=3, athlete_id=103),
            ]
        )
        self.assertEqual(len(planned), 3)

    def test_resolve_bye_advancements(self) -> None:
        rounds = plan_single_elimination([101, 102, 103])
        updated = resolve_bye_advancements(rounds)
        self.assertEqual(len(updated), len(rounds))
        # First semi is a bye in 3-athlete bracket, winner should be propagated to final slot 1.
        self.assertEqual(updated[1][0].athlete1_id, 101)

    def test_plan_single_elimination_bracket(self) -> None:
        updated = plan_single_elimination_bracket([101, 102, 103])
        self.assertEqual(len(updated), 2)
        self.assertEqual(updated[1][0].athlete1_id, 101)


if __name__ == "__main__":
    unittest.main()
