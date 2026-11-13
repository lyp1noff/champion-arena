import unittest

import httpx

from src.models import Bracket
from src.services.sync_push import (
    PendingBracket,
    SyncTransportError,
    interpret_response,
    mark_for_resend,
    retry_delay,
)


def _pending(arena_id: int, version: int = 3) -> PendingBracket:
    return PendingBracket(local_id=arena_id, arena_id=arena_id, tournament_arena_id=1, version=version, snapshot={})


class InterpretResponseTests(unittest.TestCase):
    def test_reads_per_bracket_results(self) -> None:
        response = httpx.Response(
            200,
            json={
                "results": [
                    {"bracket_id": 10, "status": "applied", "version": 3, "reason": None},
                    {"bracket_id": 11, "status": "stale", "version": 9, "reason": None},
                    {"bracket_id": 12, "status": "rejected", "version": None, "reason": "unknown_athletes:5"},
                ]
            },
        )
        results = interpret_response(response, [_pending(10), _pending(11), _pending(12)])
        self.assertEqual(results[10].status, "applied")
        self.assertEqual((results[11].status, results[11].version), ("stale", 9))
        self.assertEqual(results[12].reason, "unknown_athletes:5")

    def test_http_errors_are_transport_errors(self) -> None:
        for status in (401, 404, 422, 500, 502):
            with self.subTest(status=status), self.assertRaises(SyncTransportError):
                interpret_response(httpx.Response(status, text="nope"), [_pending(1)])

    def test_missing_or_malformed_results_are_transport_errors(self) -> None:
        with self.assertRaises(SyncTransportError):
            interpret_response(httpx.Response(200, json={"results": []}), [_pending(1)])
        with self.assertRaises(SyncTransportError):
            interpret_response(httpx.Response(200, text="<html>proxy</html>"), [_pending(1)])


class ResendTests(unittest.TestCase):
    def test_resend_after_stale_jumps_above_arena_version(self) -> None:
        bracket = Bracket(version=4, synced_version=2, sync_blocked_version=4, sync_remote_version=7, sync_error="x")
        mark_for_resend(bracket)
        self.assertEqual(bracket.version, 8)
        self.assertIsNone(bracket.synced_version)
        self.assertIsNone(bracket.sync_blocked_version)
        self.assertIsNone(bracket.sync_error)

    def test_resend_of_synced_bracket_keeps_version(self) -> None:
        bracket = Bracket(version=5, synced_version=5)
        mark_for_resend(bracket)
        self.assertEqual((bracket.version, bracket.synced_version), (5, None))


class RetryDelayTests(unittest.TestCase):
    def test_backoff_grows_and_is_capped(self) -> None:
        self.assertEqual(retry_delay(1, jitter=0), 2)
        self.assertEqual(retry_delay(3, jitter=0), 8)
        self.assertEqual(retry_delay(10_000, jitter=0), 60)
