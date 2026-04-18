import unittest
from datetime import UTC, datetime
from uuid import uuid4

from champion_domain import StructureMatchInput, build_structure_match


class StructureSnapshotTests(unittest.TestCase):
    def test_build_structure_match_main_final(self) -> None:
        match = build_structure_match(
            input_data=StructureMatchInput(
                id=str(uuid4()),
                round_number=3,
                position=1,
                next_slot=None,
                status="not_started",
                athlete1_id=1,
                athlete2_id=2,
                winner_id=None,
                score_athlete1=None,
                score_athlete2=None,
                started_at=None,
                ended_at=None,
            ),
            main_rounds=3,
        )
        self.assertEqual(match.round_type, "final")
        self.assertEqual(match.stage, "main")
        self.assertIsNone(match.repechage_side)
        self.assertIsNone(match.repechage_step)

    def test_build_structure_match_repechage(self) -> None:
        now = datetime.now(UTC)
        match = build_structure_match(
            input_data=StructureMatchInput(
                id=str(uuid4()),
                round_number=4,
                position=1,
                next_slot=1,
                status="finished",
                athlete1_id=10,
                athlete2_id=11,
                winner_id=11,
                score_athlete1=0,
                score_athlete2=3,
                started_at=now,
                ended_at=now,
            ),
            main_rounds=3,
        )
        self.assertEqual(match.round_type, "round")
        self.assertEqual(match.stage, "repechage")
        self.assertEqual(match.repechage_side, "A")
        self.assertEqual(match.repechage_step, 1)
        self.assertEqual(match.score_athlete2, 3)


if __name__ == "__main__":
    unittest.main()
