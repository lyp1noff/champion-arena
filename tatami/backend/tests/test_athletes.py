import unittest

from src.models import Athlete
from src.routers.athletes import get_local_athletes


class _FakeScalarResult:
    def __init__(self, athletes: list[Athlete]) -> None:
        self._athletes = athletes

    def all(self) -> list[Athlete]:
        return self._athletes


class _FakeResult:
    def __init__(self, athletes: list[Athlete]) -> None:
        self._athletes = athletes

    def scalars(self) -> _FakeScalarResult:
        return _FakeScalarResult(self._athletes)


class _FakeSession:
    def __init__(self, athletes: list[Athlete]) -> None:
        self._athletes = athletes

    async def execute(self, _query: object) -> _FakeResult:
        return _FakeResult(self._athletes)


class LocalAthletesTests(unittest.IsolatedAsyncioTestCase):
    async def test_returns_downloaded_athletes_with_external_ids(self) -> None:
        athlete = Athlete(
            external_id=42,
            first_name="Offline",
            last_name="Athlete",
            coaches_last_name="Coach",
        )
        athlete.id = 7

        result = await get_local_athletes(_FakeSession([athlete]))  # type: ignore[arg-type]

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, 7)
        self.assertEqual(result[0].external_id, 42)
        self.assertEqual(result[0].first_name, "Offline")


if __name__ == "__main__":
    unittest.main()
