import unittest

from champion_domain.use_cases import decide_finish_flow_post, decide_finish_flow_runtime


class FinishFlowTests(unittest.TestCase):
    def test_runtime_decision(self) -> None:
        runtime = decide_finish_flow_runtime(
            origin="local",
            stage="main",
            current_round_number=1,
            current_position=2,
            explicit_next_slot=None,
            allow_implicit_main_slot=True,
        )
        self.assertTrue(runtime.attempt_generate_repechage)
        self.assertIsNotNone(runtime.progression_action)
        assert runtime.progression_action is not None
        self.assertEqual(runtime.progression_action.kind, "main")

    def test_post_decision(self) -> None:
        post = decide_finish_flow_post(
            is_repechage_match=False,
            generated_repechage=True,
            total_matches=3,
            finished_matches=3,
            current_bracket_status="started",
        )
        self.assertTrue(post.publish_structure)
        self.assertTrue(post.completion.is_finished)
        self.assertTrue(post.completion.should_finish_bracket)


if __name__ == "__main__":
    unittest.main()
