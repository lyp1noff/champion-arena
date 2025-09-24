from datetime import datetime, timezone
from typing import List, Dict, Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models import BracketMatch, Match, MatchType, MatchStatus


async def advance_participants(db: AsyncSession, bracket_id: int) -> None:
    total_rounds: int = (
            await db.scalar(
                select(func.max(BracketMatch.round_number))
                .filter_by(bracket_id=bracket_id, match_type=MatchType.MAIN.value)
            ) or 1
    )
    repechage_depth = max(1, total_rounds - 1)

    result = await db.execute(
        select(BracketMatch)
        .filter_by(bracket_id=bracket_id)
        .options(selectinload(BracketMatch.match))
        .order_by(BracketMatch.round_number, BracketMatch.position)
    )
    matches = list(result.scalars().all())

    main_matrix: List[List[BracketMatch]] = [[] for _ in range(total_rounds)]
    repe_a: List[List[BracketMatch]] = [[] for _ in range(repechage_depth)]
    repe_b: List[List[BracketMatch]] = [[] for _ in range(repechage_depth)]

    for bm in matches:
        if bm.match_type == MatchType.MAIN.value:
            main_matrix[bm.round_number - 1].append(bm)
        elif bm.match_type == MatchType.REPECHAGE_A.value:
            repe_a[bm.round_number - 1].append(bm)
        elif bm.match_type == MatchType.REPECHAGE_B.value:
            repe_b[bm.round_number - 1].append(bm)

    await advance_main(db, main_matrix)

    semifinal_matches = [
        m for m in main_matrix[-2]
        if m.match and m.match.round_type == "semifinal" and m.match.status == MatchStatus.FINISHED.value
    ]

    if len(semifinal_matches) == 2:
        finalists = [bm.match.winner_id for bm in semifinal_matches if bm.match.winner_id]

        for finalist_id, matrix in zip(finalists, [repe_a, repe_b]):
            losers = await get_losers_to_finalist(db, finalist_id, bracket_id, total_rounds)

            for loser in losers:
                round_idx = loser["round_number"] - 1
                if 0 <= round_idx < len(matrix):
                    bm = matrix[round_idx][0]
                    m = await db.get(Match, bm.match_id)
                    if m and not m.athlete2_id:
                        m.athlete2_id = loser["loser_id"]

            await auto_advance_repechage(db, matrix)
            await advance_repechage(db, matrix)

    await db.flush()


async def advance_main(db: AsyncSession, matrix: List[List[BracketMatch]]) -> None:
    for round_index in range(len(matrix) - 1):
        for bm in matrix[round_index]:
            match = bm.match
            if not match or match.status != MatchStatus.FINISHED.value or not match.winner_id:
                continue

            next_position = (bm.position + 1) // 2
            next_bm = next((m for m in matrix[round_index + 1] if m.position == next_position), None)
            if next_bm:
                next_match = await db.get(Match, next_bm.match_id)
                if next_match:
                    if bm.position % 2 == 1:
                        next_match.athlete1_id = match.winner_id
                    else:
                        next_match.athlete2_id = match.winner_id


async def auto_advance_repechage(db: AsyncSession, matrix: List[List[BracketMatch]]) -> None:
    depth = len(matrix)
    for r in range(depth):
        bm = matrix[r][0] if matrix[r] else None
        if not bm or not bm.match:
            continue
        match = bm.match

        if match.status == MatchStatus.FINISHED.value:
            continue

        a1, a2 = match.athlete1_id, match.athlete2_id
        if (a1 and not a2) or (a2 and not a1):
            winner_id = a1 or a2
            match.winner_id = winner_id
            match.status = MatchStatus.FINISHED.value
            now = datetime.now(timezone.utc)
            if not match.started_at:
                match.started_at = now
            match.ended_at = now

            for nxt in range(r + 1, depth):
                if not matrix[nxt]:
                    continue
                next_bm = matrix[nxt][0]
                next_match = await db.get(Match, next_bm.match_id)
                if not next_match:
                    continue
                if next_match.athlete1_id is None and next_match.athlete2_id is None:
                    next_match.athlete1_id = winner_id
                    next_match.winner_id = winner_id
                    next_match.status = MatchStatus.FINISHED.value
                    if not next_match.started_at:
                        next_match.started_at = now
                    next_match.ended_at = now
                    continue
                if next_match.athlete1_id is None:
                    next_match.athlete1_id = winner_id
                elif next_match.athlete2_id is None:
                    next_match.athlete2_id = winner_id
                break


async def advance_repechage(db: AsyncSession, matrix: List[List[BracketMatch]]) -> None:
    for r in range(len(matrix) - 1):
        bm = matrix[r][0] if matrix[r] else None
        if not bm or not bm.match:
            continue
        match = bm.match
        if match.status != MatchStatus.FINISHED.value or not match.winner_id:
            continue

        winner_id = match.winner_id
        for nxt in range(r + 1, len(matrix)):
            if not matrix[nxt]:
                continue
            next_bm = matrix[nxt][0]
            next_match = await db.get(Match, next_bm.match_id)
            if not next_match:
                continue
            if next_match.athlete1_id is None:
                next_match.athlete1_id = winner_id
            elif next_match.athlete2_id is None:
                next_match.athlete2_id = winner_id
            break


async def get_losers_to_finalist(
        db: AsyncSession, finalist_id: int, bracket_id: int, total_rounds: int
) -> List[Dict[str, int]]:
    losers: List[Dict[str, int]] = []
    for round_index in range(1, total_rounds + 1):
        matches = await db.execute(
            select(BracketMatch)
            .filter_by(bracket_id=bracket_id, match_type="MAIN", round_number=round_index)
            .options(selectinload(BracketMatch.match))
        )
        for bm in matches.scalars():
            match: Optional[Match] = bm.match
            if (
                    match
                    and match.winner_id == finalist_id
                    and match.athlete1_id is not None
                    and match.athlete2_id is not None
            ):
                loser_id: int = match.athlete1_id if match.winner_id == match.athlete2_id else match.athlete2_id
                losers.append({"loser_id": loser_id, "round_number": bm.round_number})

    losers.sort(key=lambda x: x["round_number"] or 0, reverse=True)
    return losers
