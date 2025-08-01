import math
from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import (
    Bracket,
    BracketMatch,
    BracketParticipant,
    BracketType,
    Match,
    MatchStatus,
    Tournament,
)


def get_round_type(round_index: int, total_rounds: int) -> str:
    if round_index == total_rounds - 1:
        return "final"
    elif round_index == total_rounds - 2:
        return "semifinal"
    elif round_index == total_rounds - 3:
        return "quarterfinal"
    else:
        return ""


def distribute_byes_safely(athlete_ids: list[int]) -> list[tuple[Optional[int], Optional[int]]]:
    num_players = len(athlete_ids)
    next_power_of_two = 2 ** math.ceil(math.log2(max(num_players, 2)))
    total_matches = next_power_of_two // 2
    byes_needed = next_power_of_two - num_players

    ids = athlete_ids.copy()
    pairs: list[tuple[Optional[int], Optional[int]]] = []
    bye_inserted = 0
    i = 0

    # If no byes are needed, just pair up sequentially
    if byes_needed == 0:
        while i < len(ids):
            a1 = ids[i] if i < len(ids) else None
            a2 = ids[i + 1] if (i + 1) < len(ids) else None
            if a1 is None and a2 is None:
                break
            pairs.append((a1, a2))
            i += 2
        return pairs

    # Otherwise, distribute byes as evenly as possible
    insert_every = max(1, len(ids) // byes_needed) if byes_needed > 0 else 1

    while len(pairs) < total_matches:
        # Only insert a bye if we still have byes to insert
        if byes_needed > 0 and bye_inserted < byes_needed and (i // 2) % insert_every == 0:
            a1 = ids[i] if i < len(ids) else None
            pairs.append((a1, None))
            i += 1
            bye_inserted += 1
        else:
            a1 = ids[i] if i < len(ids) else None
            a2 = ids[i + 1] if (i + 1) < len(ids) else None
            if a1 is None and a2 is None:
                break
            pairs.append((a1, a2))
            i += 2

    return pairs


async def generate_first_round(
    db: AsyncSession, bracket_id: int, athlete_ids: list[int], total_rounds: int
) -> list[BracketMatch]:
    pairs = distribute_byes_safely(athlete_ids)
    matches: list[BracketMatch] = []

    for position, (a1, a2) in enumerate(pairs, start=1):
        bye = (a1 is None) != (a2 is None)
        winner_id = a1 or a2 if bye else None

        match = Match(
            athlete1_id=a1,
            athlete2_id=a2,
            winner_id=winner_id,
            round_type=get_round_type(0, total_rounds),
            status=MatchStatus.FINISHED.value if bye else MatchStatus.NOT_STARTED.value,
            ended_at=datetime.now(UTC) if bye else None,
        )
        db.add(match)
        await db.flush()

        bracket_match = BracketMatch(
            bracket_id=bracket_id,
            round_number=1,
            position=position,
            match_id=match.id,
        )
        db.add(bracket_match)
        matches.append(bracket_match)

    return matches


async def generate_following_rounds(db: AsyncSession, bracket_id: int, total_rounds: int) -> list[list[BracketMatch]]:
    match_matrix: list[list[BracketMatch]] = [[] for _ in range(total_rounds)]

    for round_num in range(2, total_rounds + 1):
        num_matches = 2 ** (total_rounds - round_num)
        for pos in range(1, num_matches + 1):
            match = Match(
                round_type=get_round_type(round_num - 1, total_rounds),
                status=MatchStatus.NOT_STARTED.value,
            )
            db.add(match)
            await db.flush()

            bracket_match = BracketMatch(
                bracket_id=bracket_id,
                round_number=round_num,
                position=pos,
                match_id=match.id,
            )
            db.add(bracket_match)
            match_matrix[round_num - 1].append(bracket_match)

    return match_matrix


async def advance_auto_winners(db: AsyncSession, match_matrix: list[list[BracketMatch]]) -> None:
    for round_index in range(len(match_matrix) - 1):
        current_round = match_matrix[round_index]
        next_round = match_matrix[round_index + 1]

        for bm in current_round:
            match = await db.get(Match, bm.match_id)

            if not match or match.status != MatchStatus.FINISHED.value or not match.winner_id:
                continue

            next_position = (bm.position + 1) // 2
            next_bm = next((m for m in next_round if m.position == next_position), None)
            if not next_bm:
                continue

            next_match = await db.get(Match, next_bm.match_id)
            if not next_match:
                continue

            if bm.position % 2 == 1:
                next_match.athlete1_id = match.winner_id if match.winner_id else None
            else:
                next_match.athlete2_id = match.winner_id if match.winner_id else None


async def regenerate_bracket_matches(
    db: AsyncSession, bracket_id: int, tournament_id: int, commit: bool = True, skip_first_round: bool = False
) -> Optional[list[list[BracketMatch]]]:
    await db.execute(
        delete(Match).where(Match.id.in_(select(BracketMatch.match_id).where(BracketMatch.bracket_id == bracket_id)))
    )
    await db.execute(delete(BracketMatch).where(BracketMatch.bracket_id == bracket_id))

    result = await db.execute(
        select(BracketParticipant).filter_by(bracket_id=bracket_id).order_by(BracketParticipant.seed)
    )
    participants = result.scalars().all()
    athlete_ids = [p.athlete_id for p in participants if p.athlete_id is not None]

    num_players = len(athlete_ids)

    # TO-DO: Return list of errors, skip category
    if num_players < 2:
        print(f"Warning! Category: {bracket_id} Player number: {num_players}")

    next_power_of_two = 2 ** math.ceil(math.log2(max(num_players, 2)))
    total_rounds = int(math.log2(next_power_of_two))

    match_matrix: list[list[BracketMatch]] = [[] for _ in range(total_rounds)]

    if not skip_first_round:
        match_matrix[0] = await generate_first_round(db, bracket_id, athlete_ids, total_rounds)

    later_rounds = await generate_following_rounds(db, bracket_id, total_rounds)
    for i in range(1, total_rounds):
        match_matrix[i] = later_rounds[i] if i < len(later_rounds) else []

    for round_index in range(len(match_matrix) - 1):
        current_round = match_matrix[round_index]
        next_round = match_matrix[round_index + 1]
        for i, match in enumerate(current_round):
            next_match_index = i // 2
            if next_match_index < len(next_round):
                match.next_slot = 1 if i % 2 == 0 else 2

    await advance_auto_winners(db, match_matrix)

    if commit:
        tournament = await db.get(Tournament, tournament_id)
        if tournament is not None:
            tournament.export_last_updated_at = datetime.now(UTC)
        await db.commit()
        return None
    else:
        return match_matrix


def split_evenly(athletes: list[BracketParticipant], max_per_group: int = 4) -> list[list[BracketParticipant]]:
    n = len(athletes)
    min_groups = math.ceil(n / max_per_group)
    base_size = n // min_groups
    extra = n % min_groups

    groups = []
    start = 0
    for i in range(min_groups):
        size = base_size + (1 if i < extra else 0)
        groups.append(athletes[start : start + size])
        start += size
    return groups


async def regenerate_round_bracket_matches(
    db: AsyncSession, bracket_id: int, tournament_id: int, commit: bool = True
) -> Optional[list[BracketMatch]]:
    await db.execute(
        delete(Match).where(Match.id.in_(select(BracketMatch.match_id).where(BracketMatch.bracket_id == bracket_id)))
    )
    await db.execute(delete(BracketMatch).where(BracketMatch.bracket_id == bracket_id))

    result = await db.execute(
        select(BracketParticipant).filter_by(bracket_id=bracket_id).order_by(BracketParticipant.seed)
    )
    participants = result.scalars().all()

    matches: list[BracketMatch] = []
    position = 1

    for i in range(len(participants)):
        for j in range(i + 1, len(participants)):
            p1 = participants[i]
            p2 = participants[j]

            match = Match(
                athlete1_id=p1.athlete_id,
                athlete2_id=p2.athlete_id,
                round_type="group",
            )
            db.add(match)
            await db.flush()

            bracket_match = BracketMatch(
                bracket_id=bracket_id,
                round_number=1,
                position=position,
                match_id=match.id,
            )
            db.add(bracket_match)
            matches.append(bracket_match)
            position += 1

    if commit:
        tournament = await db.get(Tournament, tournament_id)
        if tournament is not None:
            tournament.export_last_updated_at = datetime.now(UTC)
        await db.commit()
        return None
    else:
        return matches


async def regenerate_tournament_brackets(db: AsyncSession, tournament_id: int) -> None:
    result = await db.execute(select(Bracket.id, Bracket.type).where(Bracket.tournament_id == tournament_id))
    brackets = result.all()

    for bracket_id, bracket_type in brackets:
        if bracket_type == BracketType.ROUND_ROBIN:
            await regenerate_round_bracket_matches(db, bracket_id, tournament_id, commit=False)
        elif bracket_type == BracketType.SINGLE_ELIMINATION.value:
            await regenerate_bracket_matches(db, bracket_id, tournament_id, commit=False)
        else:
            print(f"Warning! Bracket type: {bracket_type} not supported")

    tournament = await db.get(Tournament, tournament_id)
    if tournament is not None:
        tournament.export_last_updated_at = datetime.now(UTC)
    await db.flush()
    await db.commit()


async def reorder_seeds_and_get_next(db: AsyncSession, bracket_id: int) -> int:
    result = await db.execute(
        select(BracketParticipant).where(BracketParticipant.bracket_id == bracket_id).order_by(BracketParticipant.seed)
    )
    participants = result.scalars().all()

    for index, participant in enumerate(participants, start=1):
        participant.seed = index

    await db.commit()
    return len(participants) + 1
