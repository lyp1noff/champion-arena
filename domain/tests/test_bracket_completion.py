import unittest

from champion_domain.use_cases import decide_bracket_completion, should_finish_tournament


class BracketCompletionTests(unittest.TestCase):
    def test_decide_bracket_completion_finished(self) -> None:
        decision = decide_bracket_completion(
            total_matches=5,
            finished_matches=5,
            current_bracket_status="started",
        )
        self.assertTrue(decision.is_finished)
        self.assertTrue(decision.should_finish_bracket)

    def test_decide_bracket_completion_already_finished(self) -> None:
        decision = decide_bracket_completion(
            total_matches=5,
            finished_matches=5,
            current_bracket_status="finished",
        )
        self.assertTrue(decision.is_finished)
        self.assertFalse(decision.should_finish_bracket)

    def test_decide_bracket_completion_not_finished(self) -> None:
        decision = decide_bracket_completion(
            total_matches=5,
            finished_matches=4,
            current_bracket_status="started",
        )
        self.assertFalse(decision.is_finished)
        self.assertFalse(decision.should_finish_bracket)

    def test_should_finish_tournament(self) -> None:
        self.assertTrue(should_finish_tournament(0))
        self.assertFalse(should_finish_tournament(1))
        self.assertFalse(should_finish_tournament(None))


if __name__ == "__main__":
    unittest.main()
