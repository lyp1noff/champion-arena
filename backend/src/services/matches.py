from typing import Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models import BracketMatch, Match, MatchStatus


async def advance_participants(db: AsyncSession, bracket_id: int) -> None:
    # Calculate total_rounds for the main bracket
    total_rounds: int = (
        await db.scalar(select(func.max(BracketMatch.round_number)).filter_by(bracket_id=bracket_id, match_type="MAIN"))
        or 1
    )
    repechage_depth: int = max(1, total_rounds - 1)

    # Load all matches of the bracket
    result = await db.execute(
        select(BracketMatch)
        .filter_by(bracket_id=bracket_id)
        .options(selectinload(BracketMatch.match))
        .order_by(BracketMatch.round_number, BracketMatch.position)
    )
    matches: List[BracketMatch] = list(result.scalars().all())

    # Create match_matrix with type annotation
    match_matrix: List[List[BracketMatch]] = [[] for _ in range(total_rounds + repechage_depth)]
    for m in matches:
        match_matrix[m.round_number - 1].append(m)

    # Advancement in the main bracket
    for round_index in range(total_rounds - 1):
        current_round: List[BracketMatch] = [m for m in match_matrix[round_index] if m.match_type == "MAIN"]
        next_round: List[BracketMatch] = [m for m in match_matrix[round_index + 1] if m.match_type == "MAIN"]
        for bm in current_round:
            match: Optional[Match] = bm.match
            if not match or match.status != MatchStatus.FINISHED.value or not match.winner_id:
                continue

            next_position: int = (bm.position + 1) // 2
            next_bm: Optional[BracketMatch] = next((m for m in next_round if m.position == next_position), None)
            if next_bm:
                next_match: Optional[Match] = await db.get(Match, next_bm.match_id)
                if next_match:
                    if bm.position % 2 == 1:
                        next_match.athlete1_id = match.winner_id
                    else:
                        next_match.athlete2_id = match.winner_id

    # Advancement in the repechage
    for branch in ["A", "B"]:
        for round_index in range(total_rounds, total_rounds + repechage_depth - 1):
            repechage_current_round: List[BracketMatch] = [
                m for m in match_matrix[round_index] if m.match_type == f"REPECHAGE_{branch}"
            ]
            repechage_next_round: List[BracketMatch] = [
                m for m in match_matrix[round_index + 1] if m.match_type == f"REPECHAGE_{branch}"
            ]
            for bm in repechage_current_round:
                repechage_match: Optional[Match] = bm.match
                if (
                    not repechage_match
                    or repechage_match.status != MatchStatus.FINISHED.value
                    or not repechage_match.winner_id
                ):
                    continue

                repechage_next_position: int = (bm.position + 1) // 2
                repechage_next_bm: Optional[BracketMatch] = next(
                    (m for m in repechage_next_round if m.position == repechage_next_position), None
                )
                if repechage_next_bm:
                    repechage_next_match: Optional[Match] = await db.get(Match, repechage_next_bm.match_id)
                    if repechage_next_match:
                        if bm.position % 2 == 1:
                            repechage_next_match.athlete1_id = repechage_match.winner_id
                        else:
                            repechage_next_match.athlete2_id = repechage_match.winner_id

    # Trigger repechage after semifinals
    semifinal_matches: List[BracketMatch] = [
        m
        for m in match_matrix[total_rounds - 2]
        if m.match_type == "MAIN" and m.match.round_type == "semifinal" and m.match.status == MatchStatus.FINISHED.value
    ]
    if len(semifinal_matches) == 2:
        finalists: List[int] = [bm.match.winner_id for bm in semifinal_matches if bm.match.winner_id is not None]
        for finalist_id, branch in zip(finalists, ["A", "B"]):
            losers: List[Dict[str, int]] = await get_losers_to_finalist(db, finalist_id, bracket_id, total_rounds)
            # Fix list comprehension to get a flat list
            repechage_matches: List[BracketMatch] = [
                m
                for round_matches in match_matrix[total_rounds : total_rounds + repechage_depth]
                for m in round_matches
                if m.match_type == f"REPECHAGE_{branch}"
            ]
            repechage_matches.sort(key=lambda m: (m.round_number, m.position))

            # Fill the first round of repechage
            first_round_repechage: List[BracketMatch] = [
                m for m in repechage_matches if m.round_number == total_rounds + 1
            ]
            for loser, rm in zip(losers, first_round_repechage):
                rm_match: Optional[Match] = await db.get(Match, rm.match_id)
                if rm_match:
                    if not rm_match.athlete1_id:
                        rm_match.athlete1_id = loser["loser_id"]
                    elif not rm_match.athlete2_id:
                        rm_match.athlete2_id = loser["loser_id"]

            # Fill the bronze match
            bronze_match: Optional[BracketMatch] = next(
                (m for m in repechage_matches if m.match.round_type == "bronze"), None
            )
            if bronze_match:
                bronze_match_obj: Optional[Match] = await db.get(Match, bronze_match.match_id)
                if bronze_match_obj:
                    loser_id: Optional[int] = (
                        semifinal_matches[0 if branch == "A" else 1].match.athlete1_id
                        if semifinal_matches[0 if branch == "A" else 1].match.winner_id
                        == semifinal_matches[0 if branch == "A" else 1].match.athlete2_id
                        else semifinal_matches[0 if branch == "A" else 1].match.athlete2_id
                    )
                    if loser_id is not None:
                        bronze_match_obj.athlete1_id = loser_id

                    repechage_final: Optional[BracketMatch] = next(
                        (
                            m
                            for m in repechage_matches
                            if m.match.round_type == f"round_{repechage_depth}"
                            and m.match.status == MatchStatus.FINISHED.value
                        ),
                        None,
                    )
                    if repechage_final and repechage_final.match.winner_id:
                        bronze_match_obj.athlete2_id = repechage_final.match.winner_id


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

    losers.sort(key=lambda x: x["round_number"] if x["round_number"] is not None else 0, reverse=True)
    return losers
