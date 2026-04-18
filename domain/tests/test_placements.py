import unittest

from champion_domain.use_cases import PlacementMatchInput, compute_bracket_placements


class PlacementsTests(unittest.TestCase):
    def test_no_rows(self) -> None:
        placements = compute_bracket_placements([])
        self.assertIsNone(placements.place_1_id)
        self.assertIsNone(placements.place_2_id)
        self.assertIsNone(placements.place_3_a_id)
        self.assertIsNone(placements.place_3_b_id)

    def test_main_only_bronze_from_semifinal_losses(self) -> None:
        rows = [
            PlacementMatchInput(1, "main", "finished", 10, 10, 11, None, None),
            PlacementMatchInput(1, "main", "finished", 20, 20, 21, None, None),
            PlacementMatchInput(2, "main", "finished", 10, 10, 20, None, None),
        ]
        placements = compute_bracket_placements(rows)
        self.assertEqual(placements.place_1_id, 10)
        self.assertEqual(placements.place_2_id, 20)
        self.assertEqual(placements.place_3_a_id, 11)
        self.assertEqual(placements.place_3_b_id, 21)

    def test_repechage_overrides_direct_bronze(self) -> None:
        rows = [
            PlacementMatchInput(1, "main", "finished", 10, 10, 11, None, None),
            PlacementMatchInput(1, "main", "finished", 20, 20, 21, None, None),
            PlacementMatchInput(2, "main", "finished", 10, 10, 20, None, None),
            PlacementMatchInput(3, "repechage", "finished", 31, 11, 31, "A", 1),
            PlacementMatchInput(3, "repechage", "finished", 41, 21, 41, "B", 1),
        ]
        placements = compute_bracket_placements(rows)
        self.assertEqual(placements.place_3_a_id, 31)
        self.assertEqual(placements.place_3_b_id, 41)

    def test_prevent_duplicate_places(self) -> None:
        rows = [
            PlacementMatchInput(1, "main", "finished", 10, 10, 11, None, None),
            PlacementMatchInput(1, "main", "finished", 20, 20, 21, None, None),
            PlacementMatchInput(2, "main", "finished", 10, 10, 20, None, None),
            # Bad data case: repechage winner equals champion.
            PlacementMatchInput(3, "repechage", "finished", 10, 11, 10, "A", 1),
        ]
        placements = compute_bracket_placements(rows)
        self.assertEqual(placements.place_1_id, 10)
        self.assertEqual(placements.place_2_id, 20)
        self.assertIsNone(placements.place_3_a_id)


if __name__ == "__main__":
    unittest.main()
