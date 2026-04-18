import unittest

from champion_domain.use_cases import decide_finish_runtime


class FinishRuntimeTests(unittest.TestCase):
    def test_main_local_runtime_decision(self) -> None:
        decision = decide_finish_runtime(
            origin="local",
            stage="main",
            current_round_number=1,
            current_position=2,
            explicit_next_slot=None,
            allow_implicit_main_slot=True,
        )
        self.assertTrue(decision.attempt_generate_repechage)
        self.assertIsNotNone(decision.progression_action)
        assert decision.progression_action is not None
        self.assertEqual(decision.progression_action.kind, "main")
        self.assertEqual(decision.progression_action.main_round_number, 2)
        self.assertEqual(decision.progression_action.main_position, 1)
        self.assertEqual(decision.progression_action.slot, 2)

    def test_repechage_sync_runtime_decision(self) -> None:
        decision = decide_finish_runtime(
            origin="sync",
            stage="repechage",
            current_round_number=4,
            current_position=1,
            explicit_next_slot=None,
            repechage_side="A",
            repechage_step=1,
            main_rounds=3,
        )
        self.assertFalse(decision.attempt_generate_repechage)
        self.assertIsNotNone(decision.progression_action)
        assert decision.progression_action is not None
        self.assertEqual(decision.progression_action.kind, "repechage")
        self.assertEqual(decision.progression_action.repechage_round_number, 5)
        self.assertEqual(decision.progression_action.repechage_position, 1)


if __name__ == "__main__":
    unittest.main()
