import unittest

import httpx

from src.services.outbox_delivery import (
    ClaimedOutboxItem,
    DeliveryFailure,
    OutboxTransport,
    classify_sync_response,
    retry_delay,
)


class OutboxDeliveryTests(unittest.IsolatedAsyncioTestCase):
    def test_accepted_and_duplicate_responses_succeed(self) -> None:
        classify_sync_response(httpx.Response(200, json={"accepted": [1], "duplicates": [], "conflicts": []}))
        classify_sync_response(httpx.Response(200, json={"accepted": [], "duplicates": [1], "conflicts": []}))

    def test_application_conflict_is_terminal(self) -> None:
        response = httpx.Response(
            200,
            json={"accepted": [], "duplicates": [], "conflicts": [{"reason": "version_conflict"}]},
        )
        with self.assertRaises(DeliveryFailure) as raised:
            classify_sync_response(response)
        self.assertFalse(raised.exception.retryable)
        self.assertEqual(raised.exception.kind, "application")

    def test_transport_statuses_are_retryable_without_attempt_limit(self) -> None:
        for status in (408, 409, 429, 500, 503):
            with self.subTest(status=status), self.assertRaises(DeliveryFailure) as raised:
                classify_sync_response(httpx.Response(status, text="temporary"))
            self.assertTrue(raised.exception.retryable)

        self.assertGreaterEqual(retry_delay(10_000, jitter=0), 60)
        self.assertLessEqual(retry_delay(10_000, jitter=1), 61)

    def test_validation_status_is_terminal(self) -> None:
        with self.assertRaises(DeliveryFailure) as raised:
            classify_sync_response(httpx.Response(422, text="invalid payload"))
        self.assertFalse(raised.exception.retryable)
        self.assertEqual(raised.exception.kind, "http_rejection")

    def test_invalid_success_body_is_retryable_protocol_failure(self) -> None:
        with self.assertRaises(DeliveryFailure) as raised:
            classify_sync_response(httpx.Response(200, json=[]))
        self.assertTrue(raised.exception.retryable)
        self.assertEqual(raised.exception.kind, "protocol")

    async def test_network_failure_is_retryable(self) -> None:
        async def fail(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("offline", request=request)

        client = httpx.AsyncClient(transport=httpx.MockTransport(fail))
        transport = OutboxTransport(client)
        with self.assertRaises(DeliveryFailure) as raised:
            await transport.deliver(ClaimedOutboxItem(id=1, payload="{}", retry_count=500))
        self.assertTrue(raised.exception.retryable)
        self.assertEqual(raised.exception.kind, "network")
        await client.aclose()


if __name__ == "__main__":
    unittest.main()
