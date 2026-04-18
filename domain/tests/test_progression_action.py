import unittest

from champion_domain.use_cases import compute_progression_action


class ProgressionActionTests(unittest.TestCase):
    def test_main_progression_action(self) -> None:
        action = compute_progression_action(
            stage="main",
            current_round_number=1,
            current_position=2,
            explicit_next_slot=None,
            allow_implicit_main_slot=True,
        )
        self.assertIsNotNone(action)
        assert action is not None
        self.assertEqual(action.kind, "main")
        self.assertEqual(action.main_round_number, 2)
        self.assertEqual(action.main_position, 1)
        self.assertEqual(action.slot, 2)

    def test_repechage_progression_action_with_main_rounds(self) -> None:
        action = compute_progression_action(
            stage="repechage",
            current_round_number=4,
            current_position=1,
            explicit_next_slot=None,
            repechage_side="A",
            repechage_step=1,
            main_rounds=3,
        )
        self.assertIsNotNone(action)
        assert action is not None
        self.assertEqual(action.kind, "repechage")
        self.assertEqual(action.repechage_side, "A")
        self.assertEqual(action.repechage_step, 2)
        self.assertEqual(action.repechage_round_number, 5)
        self.assertEqual(action.repechage_position, 1)


if __name__ == "__main__":
    unittest.main()
