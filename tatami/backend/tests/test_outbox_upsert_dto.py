import unittest
from datetime import UTC, datetime
from uuid import uuid4

from src.services.outbox_upsert_dto import make_sync_upserts_envelope


class OutboxUpsertDTOTests(unittest.TestCase):
    def test_event_identity_is_preserved_in_serialized_envelope(self) -> None:
        event_id = uuid4()
        envelope = make_sync_upserts_envelope(
            edge_id="tatami-1",
            tournament_id=7,
            event_id=event_id,
            seq=42,
            item_type="match.upsert",
            aggregate_id="match-1",
            aggregate_version=3,
            occurred_at=datetime.now(UTC),
            payload={"status": "started"},
        )
        self.assertEqual(envelope["items"][0]["event_id"], str(event_id))
        self.assertEqual(envelope["items"][0]["seq"], 42)
        self.assertEqual(envelope["tournament_id"], 7)


if __name__ == "__main__":
    unittest.main()
