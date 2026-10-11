import unittest
from unittest.mock import AsyncMock, patch

from src.services.sync import rebootstrap_tournament


class _FakeSession:
    def __init__(self) -> None:
        self.commit = AsyncMock()
        self.rollback = AsyncMock()


class RebootstrapTests(unittest.IsolatedAsyncioTestCase):
    async def test_does_not_commit_deletion_before_snapshot_import(self) -> None:
        db = _FakeSession()

        with (
            patch("src.services.sync.reset_local_tournament_copy", new=AsyncMock(return_value=True)) as reset,
            patch(
                "src.services.sync.sync_tournament",
                new=AsyncMock(return_value={"status": "error", "message": "Arena unavailable"}),
            ) as sync,
        ):
            result = await rebootstrap_tournament(42, db)  # type: ignore[arg-type]

        reset.assert_awaited_once_with(42, db)
        sync.assert_awaited_once_with(42, db)
        db.commit.assert_not_awaited()
        self.assertEqual(result["status"], "error")


if __name__ == "__main__":
    unittest.main()
