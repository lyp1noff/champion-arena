import unittest

from champion_domain import classify_bracket_match, compute_main_rounds


class BracketLabelsTests(unittest.TestCase):
    def test_compute_main_rounds(self) -> None:
        self.assertEqual(compute_main_rounds(None), 0)
        self.assertEqual(compute_main_rounds(1), 0)
        self.assertEqual(compute_main_rounds(2), 1)
        self.assertEqual(compute_main_rounds(6), 3)
        self.assertEqual(compute_main_rounds(8), 3)

    def test_classify_main_final(self) -> None:
        item = classify_bracket_match(round_number=3, position=1, main_rounds=3)
        self.assertFalse(item.is_repechage)
        self.assertEqual(item.stage, "main")
        self.assertEqual(item.round_type, "final")
        self.assertIsNone(item.repechage_side)
        self.assertIsNone(item.repechage_step)

    def test_classify_repechage(self) -> None:
        item = classify_bracket_match(round_number=4, position=2, main_rounds=3)
        self.assertTrue(item.is_repechage)
        self.assertEqual(item.stage, "repechage")
        self.assertEqual(item.round_type, "round")
        self.assertEqual(item.repechage_side, "B")
        self.assertEqual(item.repechage_step, 1)


if __name__ == "__main__":
    unittest.main()
