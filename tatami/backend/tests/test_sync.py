import unittest
from unittest.mock import AsyncMock, patch

from src.services.sync import rebootstrap_tournament


class _FakeSession:
    def __init__(self) -> None:
        self.commit = AsyncMock()
        self.rollback = AsyncMock()


class RebootstrapTests(unittest.IsolatedAsyncioTestCase):
    async def test_leaves_local_copy_untouched_when_arena_is_unavailable(self) -> None:
        db = _FakeSession()

        with (
            patch(
                "src.services.sync.fetch_bootstrap_snapshot",
                new=AsyncMock(side_effect=RuntimeError("Arena unavailable")),
            ) as fetch,
            patch("src.services.sync.reset_local_tournament_copy", new=AsyncMock(return_value=True)) as reset,
        ):
            result = await rebootstrap_tournament(42, db)  # type: ignore[arg-type]

        fetch.assert_awaited_once_with(42)
        reset.assert_not_awaited()
        db.commit.assert_not_awaited()
        self.assertEqual(result["status"], "error")

    async def test_rolls_back_deletion_when_snapshot_import_fails(self) -> None:
        db = _FakeSession()

        with (
            patch("src.services.sync.fetch_bootstrap_snapshot", new=AsyncMock(return_value={"tournament": {}})),
            patch("src.services.sync.reset_local_tournament_copy", new=AsyncMock(return_value=True)) as reset,
            patch(
                "src.services.sync._import_bootstrap_snapshot",
                new=AsyncMock(side_effect=ValueError("invalid snapshot")),
            ),
        ):
            result = await rebootstrap_tournament(42, db)  # type: ignore[arg-type]

        reset.assert_awaited_once_with(42, db)
        db.commit.assert_not_awaited()
        db.rollback.assert_awaited_once()
        self.assertEqual(result["status"], "error")


if __name__ == "__main__":
    unittest.main()
