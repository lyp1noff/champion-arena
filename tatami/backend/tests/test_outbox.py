import json
import unittest

from src.services.outbox import create_outbox_entry


class _FakeSession:
    def __init__(self) -> None:
        self.added = []
        self.flush_count = 0

    def add(self, item: object) -> None:
        self.added.append(item)

    async def flush(self) -> None:
        self.flush_count += 1
        if self.flush_count == 1:
            self.added[0].id = 42


class OutboxTests(unittest.IsolatedAsyncioTestCase):
    async def test_create_outbox_entry_uses_local_id_for_fk_and_external_id_for_payload(self) -> None:
        db = _FakeSession()

        item = await create_outbox_entry(
            db=db,
            item_type="match.upsert",
            aggregate_id="match-1",
            aggregate_version=3,
            payload={"status": "started"},
            local_tournament_id=1,
            external_tournament_id=6,
            match_id=99,
        )

        self.assertEqual(item.tournament_id, 1)
        self.assertEqual(item.match_id, 99)

        envelope = json.loads(item.payload)
        self.assertEqual(envelope["tournament_id"], 6)
        self.assertEqual(envelope["items"][0]["seq"], 42)


if __name__ == "__main__":
    unittest.main()
