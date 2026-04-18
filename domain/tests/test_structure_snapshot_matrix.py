import unittest
from uuid import uuid4

from champion_domain import StructureMatchInput, build_structure_match, compute_main_rounds


class StructureSnapshotMatrixTests(unittest.TestCase):
    def _labels(self, participants_count: int, rounds: list[int]) -> list[tuple[str, str, str | None, int | None]]:
        main_rounds = compute_main_rounds(participants_count)
        items = []
        for round_number in rounds:
            match = build_structure_match(
                input_data=StructureMatchInput(
                    id=str(uuid4()),
                    round_number=round_number,
                    position=1,
                    next_slot=1 if round_number < max(rounds) else None,
                    status="not_started",
                    athlete1_id=None,
                    athlete2_id=None,
                    winner_id=None,
                    score_athlete1=None,
                    score_athlete2=None,
                    started_at=None,
                    ended_at=None,
                ),
                main_rounds=main_rounds,
            )
            items.append((match.stage, match.round_type or "", match.repechage_side, match.repechage_step))
        return items

    def test_labels_for_8_participants_main(self) -> None:
        labels = self._labels(participants_count=8, rounds=[1, 2, 3])
        self.assertEqual(labels[0][0], "main")
        self.assertEqual(labels[0][1], "quarterfinal")
        self.assertEqual(labels[1][1], "semifinal")
        self.assertEqual(labels[2][1], "final")

    def test_labels_for_6_participants_with_repechage(self) -> None:
        labels = self._labels(participants_count=6, rounds=[1, 2, 3, 4])
        self.assertEqual(labels[0][1], "quarterfinal")
        self.assertEqual(labels[1][1], "semifinal")
        self.assertEqual(labels[2][1], "final")
        self.assertEqual(labels[3][0], "repechage")
        self.assertEqual(labels[3][1], "round")
        self.assertEqual(labels[3][2], "A")
        self.assertEqual(labels[3][3], 1)


if __name__ == "__main__":
    unittest.main()
