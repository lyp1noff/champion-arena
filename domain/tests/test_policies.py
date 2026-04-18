import unittest
from dataclasses import dataclass

from champion_domain import bump_bracket_version, final_loser_id, match_loser_id


@dataclass
class BracketStub:
    version: int | None


@dataclass
class MatchStub:
    winner_id: int | None
    athlete1_id: int | None
    athlete2_id: int | None


class PolicyTests(unittest.TestCase):
    def test_bump_bracket_version(self) -> None:
        bracket = BracketStub(version=3)
        bump_bracket_version(bracket)
        self.assertEqual(bracket.version, 4)

        bracket_none = BracketStub(version=None)
        bump_bracket_version(bracket_none)
        self.assertEqual(bracket_none.version, 1)

    def test_match_loser_id_from_match_object(self) -> None:
        match = MatchStub(winner_id=10, athlete1_id=10, athlete2_id=20)
        self.assertEqual(match_loser_id(match), 20)
        self.assertEqual(final_loser_id(match), 20)

    def test_match_loser_id_from_explicit_values(self) -> None:
        self.assertEqual(match_loser_id(10, 10, 20), 20)
        self.assertEqual(final_loser_id(20, 10, 20), 10)


if __name__ == "__main__":
    unittest.main()
