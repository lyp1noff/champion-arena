#!/usr/bin/env python3
import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.orm import selectinload

PROJECT_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_BACKEND_ROOT))

from src.database import SessionLocal  # noqa: E402
from src.models import Athlete, Bracket, BracketMatch, Match, OutboxItem  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Decode non-success outbox_items payload and enrich IDs with human-readable data."
    )
    parser.add_argument("--limit", type=int, default=100, help="How many outbox rows to print (default: 100)")
    parser.add_argument(
        "--status-not",
        default="success",
        help="Exclude rows with this status (default: success)",
    )
    parser.add_argument(
        "--statuses",
        default="",
        help="Optional comma-separated statuses to include (e.g. failed,pending,processing)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    return parser.parse_args()


def try_int(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None


def parse_payload(raw_payload: str | None) -> dict[str, Any] | None:
    if not raw_payload:
        return None
    try:
        parsed = json.loads(raw_payload)
    except json.JSONDecodeError:
        return None
    if isinstance(parsed, dict):
        return parsed
    return None


def extract_event(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if not payload:
        return None
    events = payload.get("events")
    if isinstance(events, list) and events and isinstance(events[0], dict):
        return events[0]
    return None


def collect_lookup_ids(
    row: OutboxItem,
    event: dict[str, Any] | None,
    athlete_external_ids: set[int],
    bracket_external_ids: set[int],
    match_external_ids: set[str],
) -> None:
    if event is None:
        return

    aggregate_type = event.get("aggregate_type")
    aggregate_id = event.get("aggregate_id")

    if aggregate_type == "bracket":
        bracket_id = try_int(aggregate_id)
        if bracket_id is not None:
            bracket_external_ids.add(bracket_id)
    elif aggregate_type == "match" and isinstance(aggregate_id, str):
        match_external_ids.add(aggregate_id)

    payload_data = event.get("payload")
    if not isinstance(payload_data, dict):
        return

    winner_id = try_int(payload_data.get("winner_id"))
    if winner_id is not None:
        athlete_external_ids.add(winner_id)

    participants = payload_data.get("participants")
    if isinstance(participants, list):
        for participant in participants:
            if not isinstance(participant, dict):
                continue
            athlete_id = try_int(participant.get("athlete_id"))
            if athlete_id is not None:
                athlete_external_ids.add(athlete_id)

    matches = payload_data.get("matches")
    if isinstance(matches, list):
        for match_data in matches:
            if not isinstance(match_data, dict):
                continue
            match_id = match_data.get("id")
            if isinstance(match_id, str):
                match_external_ids.add(match_id)
            for key in ("athlete1_id", "athlete2_id", "winner_id"):
                athlete_id = try_int(match_data.get(key))
                if athlete_id is not None:
                    athlete_external_ids.add(athlete_id)

    if row.match is not None:
        for bm in row.match.bracket_matches:
            if bm.bracket is not None:
                bracket_external_ids.add(bm.bracket.external_id)


def athlete_name(external_id: int | None, athletes_by_external_id: dict[int, Athlete]) -> str | None:
    if external_id is None:
        return None
    athlete = athletes_by_external_id.get(external_id)
    if athlete is None:
        return f"UNKNOWN athlete (external_id={external_id})"
    return f"{athlete.last_name} {athlete.first_name} (external_id={external_id})"


def bracket_info(external_id: int | None, brackets_by_external_id: dict[int, Bracket]) -> dict[str, Any] | None:
    if external_id is None:
        return None
    bracket = brackets_by_external_id.get(external_id)
    if bracket is None:
        return {"external_id": external_id, "label": "UNKNOWN bracket"}
    return {
        "external_id": bracket.external_id,
        "display_name": bracket.display_name,
        "category": bracket.category,
        "status": bracket.status,
        "state": bracket.state,
        "tournament_id": bracket.tournament_id,
    }


def decode_payload_human(
    event: dict[str, Any] | None,
    athletes_by_external_id: dict[int, Athlete],
) -> dict[str, Any] | None:
    if event is None:
        return None

    payload_data = event.get("payload")
    if not isinstance(payload_data, dict):
        return None

    result: dict[str, Any] = dict(payload_data)

    winner_id = try_int(payload_data.get("winner_id"))
    if winner_id is not None:
        result["winner_name"] = athlete_name(winner_id, athletes_by_external_id)

    participants = payload_data.get("participants")
    if isinstance(participants, list):
        decoded_participants: list[dict[str, Any]] = []
        for participant in participants:
            if not isinstance(participant, dict):
                continue
            athlete_id = try_int(participant.get("athlete_id"))
            item = dict(participant)
            item["athlete_name"] = athlete_name(athlete_id, athletes_by_external_id)
            decoded_participants.append(item)
        result["participants"] = decoded_participants

    matches = payload_data.get("matches")
    if isinstance(matches, list):
        decoded_matches: list[dict[str, Any]] = []
        for match_data in matches:
            if not isinstance(match_data, dict):
                continue
            item = dict(match_data)
            athlete1_id = try_int(match_data.get("athlete1_id"))
            athlete2_id = try_int(match_data.get("athlete2_id"))
            winner_ext_id = try_int(match_data.get("winner_id"))
            item["athlete1_name"] = athlete_name(athlete1_id, athletes_by_external_id)
            item["athlete2_name"] = athlete_name(athlete2_id, athletes_by_external_id)
            item["winner_name"] = athlete_name(winner_ext_id, athletes_by_external_id)
            decoded_matches.append(item)
        result["matches"] = decoded_matches

    return result


def resolve_bracket_external_id(
    row: OutboxItem,
    event: dict[str, Any] | None,
    matches_by_external_id: dict[str, Match],
) -> int | None:
    if event is not None:
        aggregate_type = event.get("aggregate_type")
        aggregate_id = event.get("aggregate_id")

        if aggregate_type == "bracket":
            return try_int(aggregate_id)

        if aggregate_type == "match" and isinstance(aggregate_id, str):
            match = matches_by_external_id.get(aggregate_id)
            if match is not None and match.bracket_matches:
                bracket = match.bracket_matches[0].bracket
                if bracket is not None:
                    return bracket.external_id

    if row.match is not None and row.match.bracket_matches:
        bracket = row.match.bracket_matches[0].bracket
        if bracket is not None:
            return bracket.external_id

    return None


async def run() -> None:
    args = parse_args()
    statuses = [value.strip() for value in args.statuses.split(",") if value.strip()]

    async with SessionLocal() as db:
        query = (
            select(OutboxItem)
            .options(
                selectinload(OutboxItem.match).selectinload(Match.bracket_matches).selectinload(BracketMatch.bracket)
            )
            .order_by(desc(OutboxItem.created_at))
            .limit(args.limit)
        )

        if args.status_not:
            query = query.where(OutboxItem.status != args.status_not)
        if statuses:
            query = query.where(OutboxItem.status.in_(statuses))

        rows = (await db.execute(query)).scalars().all()

        athlete_external_ids: set[int] = set()
        bracket_external_ids: set[int] = set()
        match_external_ids: set[str] = set()
        parsed_rows: list[tuple[OutboxItem, dict[str, Any] | None, dict[str, Any] | None]] = []

        for row in rows:
            payload = parse_payload(row.payload)
            event = extract_event(payload)
            collect_lookup_ids(row, event, athlete_external_ids, bracket_external_ids, match_external_ids)
            parsed_rows.append((row, payload, event))

        athletes_by_external_id: dict[int, Athlete] = {}
        if athlete_external_ids:
            athletes_result = await db.execute(select(Athlete).where(Athlete.external_id.in_(athlete_external_ids)))
            athletes_by_external_id = {athlete.external_id: athlete for athlete in athletes_result.scalars().all()}

        brackets_by_external_id: dict[int, Bracket] = {}
        if bracket_external_ids:
            brackets_result = await db.execute(select(Bracket).where(Bracket.external_id.in_(bracket_external_ids)))
            brackets_by_external_id = {bracket.external_id: bracket for bracket in brackets_result.scalars().all()}

        matches_by_external_id: dict[str, Match] = {}
        if match_external_ids:
            matches_result = await db.execute(
                select(Match)
                .where(Match.external_id.in_(match_external_ids))
                .options(
                    selectinload(Match.bracket_matches).selectinload(BracketMatch.bracket),
                    selectinload(Match.athlete1),
                    selectinload(Match.athlete2),
                )
            )
            matches_by_external_id = {match.external_id: match for match in matches_result.scalars().all()}

        decoded_items: list[dict[str, Any]] = []
        for row, payload, event in parsed_rows:
            bracket_external_id = resolve_bracket_external_id(row, event, matches_by_external_id)
            resolved_bracket = bracket_info(bracket_external_id, brackets_by_external_id)

            event_type = event.get("event_type") if event else None
            aggregate_type = event.get("aggregate_type") if event else None
            aggregate_id = event.get("aggregate_id") if event else None

            decoded = {
                "outbox_item_id": row.id,
                "status": row.status,
                "retry_count": row.retry_count,
                "max_retries": row.max_retries,
                "error": row.error,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "updated_at": row.updated_at.isoformat() if row.updated_at else None,
                "endpoint": row.endpoint,
                "method": row.method,
                "event_type": event_type,
                "aggregate_type": aggregate_type,
                "aggregate_id": aggregate_id,
                "edge_id": payload.get("edge_id") if payload else None,
                "bracket": resolved_bracket,
                "payload_human": decode_payload_human(event, athletes_by_external_id),
            }

            if aggregate_type == "match" and isinstance(aggregate_id, str):
                match = matches_by_external_id.get(aggregate_id)
                if match is not None:
                    decoded["match"] = {
                        "external_id": match.external_id,
                        "status": match.status,
                        "athlete1": athlete_name(
                            match.athlete1.external_id if match.athlete1 is not None else None, athletes_by_external_id
                        ),
                        "athlete2": athlete_name(
                            match.athlete2.external_id if match.athlete2 is not None else None, athletes_by_external_id
                        ),
                    }

            decoded_items.append(decoded)

    if args.format == "json":
        print(json.dumps(decoded_items, ensure_ascii=False, indent=2))
        return

    if not decoded_items:
        print("No outbox_items matched filters.")
        return

    for item in decoded_items:
        print("=" * 120)
        print(
            f"OutboxItem #{item['outbox_item_id']} | status={item['status']}",
            "| retries={item['retry_count']}/{item['max_retries']}",
        )
        print(f"Event: {item['event_type']} | aggregate={item['aggregate_type']}:{item['aggregate_id']}")
        print(f"Created: {item['created_at']}")
        if item["error"]:
            print(f"Error: {item['error']}")
        if item["bracket"]:
            bracket = item["bracket"]
            print(
                "Bracket: "
                f"external_id={bracket.get('external_id')} | category={bracket.get('category')} | "
                f"display_name={bracket.get('display_name')}"
            )
        print("Payload (human):")
        print(json.dumps(item["payload_human"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(run())
