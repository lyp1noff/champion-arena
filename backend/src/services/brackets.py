import math
from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.logger import logger
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

    pairs: list[tuple[Optional[int], Optional[int]]] = []
    ids = athlete_ids.copy()

    bye_positions = set()
    if byes_needed > 0:
        step = total_matches / byes_needed
        for k in range(byes_needed):
            pos = round(k * step)
            bye_positions.add(pos)

    idx = 0
    for match_idx in range(total_matches):
        if match_idx in bye_positions and idx < len(ids):
            pairs.append((ids[idx], None))
            idx += 1
        else:
            a1 = ids[idx] if idx < len(ids) else None
            a2 = ids[idx + 1] if (idx + 1) < len(ids) else None
            pairs.append((a1, a2))
            idx += 2

    return pairs


async def generate_all_rounds(
    db: AsyncSession, bracket_id: int, athlete_ids: list[int], total_rounds: int
) -> list[list[BracketMatch]]:
    match_matrix: list[list[BracketMatch]] = [[] for _ in range(total_rounds)]

    pairs = distribute_byes_safely(athlete_ids)
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
        match_matrix[0].append(bracket_match)

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


async def regenerate_bracket_matches(
    db: AsyncSession, bracket_id: int, tournament_id: int, commit: bool = True
) -> None:
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
    if num_players < 2:
        logger.warning(f"Category: {bracket_id} Player number: {num_players}")
        if commit:
            tournament = await db.get(Tournament, tournament_id)
            if tournament is not None:
                tournament.export_last_updated_at = datetime.now(UTC)
            await db.commit()
        return None

    next_power_of_two = 2 ** math.ceil(math.log2(max(num_players, 2)))
    total_rounds = int(math.log2(next_power_of_two))

    match_matrix = await generate_all_rounds(db, bracket_id, athlete_ids, total_rounds)

    for round_index in range(total_rounds - 1):
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
    n = len(participants)

    matches: list[BracketMatch] = []
    if n < 2:
        if commit:
            tournament = await db.get(Tournament, tournament_id)
            if tournament is not None:
                tournament.export_last_updated_at = datetime.now(UTC)
            await db.commit()
        return None if commit else matches

    participants = list(participants)
    if n % 2 != 0:
        dummy = BracketParticipant(athlete_id=None, bracket_id=bracket_id, seed=n + 1)
        participants.append(dummy)
        n += 1

    players = list(range(n))
    rounds = []
    for _ in range(n - 1):
        round_pairs = []
        mid = n // 2
        for i in range(mid):
            p1_idx, p2_idx = players[i], players[n - 1 - i]
            if participants[p1_idx].athlete_id is None or participants[p2_idx].athlete_id is None:
                continue
            if participants[p1_idx].seed < participants[p2_idx].seed:
                round_pairs.append((p1_idx, p2_idx))
            else:
                round_pairs.append((p2_idx, p1_idx))
        rounds.append(round_pairs)
        players = [players[0]] + [players[-1]] + players[1:-1]

    position = 1
    for round_pairs in rounds:
        for p1_idx, p2_idx in round_pairs:
            p1 = participants[p1_idx]
            p2 = participants[p2_idx]
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
        if bracket_type == BracketType.ROUND_ROBIN.value:
            await regenerate_round_bracket_matches(db, bracket_id, tournament_id, commit=False)
        elif bracket_type == BracketType.SINGLE_ELIMINATION.value:
            await regenerate_bracket_matches(db, bracket_id, tournament_id, commit=False)
        else:
            logger.warning(f"Bracket type: {bracket_type} not supported")

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
