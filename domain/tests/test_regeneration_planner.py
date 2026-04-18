import unittest

from champion_domain.use_cases import SeededParticipant, plan_bracket_matches


class RegenerationPlannerTests(unittest.TestCase):
    def test_plan_single_elimination_matches(self) -> None:
        planned = plan_bracket_matches(
            "single_elimination",
            [
                SeededParticipant(seed=1, athlete_id=101),
                SeededParticipant(seed=2, athlete_id=102),
                SeededParticipant(seed=3, athlete_id=103),
            ],
        )
        self.assertEqual(len(planned), 3)
        final = max(planned, key=lambda item: item.round_number)
        self.assertEqual(final.round_type, "final")
        self.assertEqual(final.athlete1_id, 101)

    def test_plan_round_robin_matches(self) -> None:
        planned = plan_bracket_matches(
            "round_robin",
            [
                SeededParticipant(seed=1, athlete_id=101),
                SeededParticipant(seed=2, athlete_id=102),
                SeededParticipant(seed=3, athlete_id=103),
            ],
        )
        self.assertEqual(len(planned), 3)
        self.assertTrue(all(item.round_type == "group" for item in planned))
        self.assertTrue(all(item.next_slot is None for item in planned))

    def test_plan_unsupported_type(self) -> None:
        with self.assertRaises(ValueError):
            plan_bracket_matches("swiss", [SeededParticipant(seed=1, athlete_id=101)])


if __name__ == "__main__":
    unittest.main()
