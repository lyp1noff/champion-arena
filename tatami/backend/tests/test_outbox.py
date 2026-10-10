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
        self.assertFalse(hasattr(item, "max_retries"))
        self.assertFalse(hasattr(item, "endpoint"))

        envelope = json.loads(item.payload)
        self.assertEqual(envelope["tournament_id"], 6)
        self.assertEqual(envelope["items"][0]["seq"], 42)

    async def test_reconciliation_creates_a_new_event_identity(self) -> None:
        first = await create_outbox_entry(
            db=_FakeSession(),
            item_type="match.upsert",
            aggregate_id="match-1",
            aggregate_version=3,
            payload={"status": "started"},
            local_tournament_id=1,
            external_tournament_id=6,
        )
        reconciled = await create_outbox_entry(
            db=_FakeSession(),
            item_type="match.upsert",
            aggregate_id="match-1",
            aggregate_version=3,
            payload={"status": "started"},
            local_tournament_id=1,
            external_tournament_id=6,
        )

        first_event_id = json.loads(first.payload)["items"][0]["event_id"]
        reconciled_event_id = json.loads(reconciled.payload)["items"][0]["event_id"]
        self.assertNotEqual(first_event_id, reconciled_event_id)


if __name__ == "__main__":
    unittest.main()
