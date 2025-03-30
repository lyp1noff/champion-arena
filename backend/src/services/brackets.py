import math
from typing import Optional
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models import Bracket, BracketParticipant, BracketMatch, Match


def get_round_type(round_index: int, total_rounds: int) -> str:
    if round_index == total_rounds - 1:
        return "final"
    elif round_index == total_rounds - 2:
        return "semifinal"
    elif round_index == total_rounds - 3:
        return "quarterfinal"
    else:
        return ""


def distribute_byes_safely(
    athlete_ids: list[int],
) -> list[tuple[Optional[int], Optional[int]]]:
    num_players = len(athlete_ids)
    next_power_of_two = 2 ** math.ceil(math.log2(max(num_players, 2)))
    total_matches = next_power_of_two // 2
    byes_needed = next_power_of_two - num_players

    ids = athlete_ids.copy()
    pairs = []
    insert_every = max(1, len(ids) // byes_needed) if byes_needed else None
    bye_inserted = 0
    i = 0

    while len(pairs) < total_matches:
        if byes_needed and bye_inserted < byes_needed and (i // 2) % insert_every == 0:
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
    session: AsyncSession, bracket_id: int, athlete_ids: list[int], total_rounds: int
):
    pairs = distribute_byes_safely(athlete_ids)
    matches = []

    for position, (a1, a2) in enumerate(pairs, start=1):
        match = Match(
            athlete1_id=a1,
            athlete2_id=a2,
            round_type=get_round_type(0, total_rounds),
        )
        if (a1 is None) != (a2 is None):
            match.winner_id = a1 or a2
            match.is_finished = True

        session.add(match)
        await session.flush()

        bracket_match = BracketMatch(
            bracket_id=bracket_id,
            round_number=1,
            position=position,
            match_id=match.id,
        )
        session.add(bracket_match)
        matches.append(bracket_match)

    return matches


async def generate_following_rounds(
    session: AsyncSession, bracket_id: int, total_rounds: int
):
    match_matrix = [[] for _ in range(total_rounds)]

    for round_num in range(2, total_rounds + 1):
        num_matches = 2 ** (total_rounds - round_num)
        for pos in range(1, num_matches + 1):
            match = Match(round_type=get_round_type(round_num - 1, total_rounds))
            session.add(match)
            await session.flush()

            bracket_match = BracketMatch(
                bracket_id=bracket_id,
                round_number=round_num,
                position=pos,
                match_id=match.id,
            )
            session.add(bracket_match)
            match_matrix[round_num - 1].append(bracket_match)

    return match_matrix


async def advance_auto_winners(
    session: AsyncSession, match_matrix: list[list[BracketMatch]]
):
    for round_index in range(len(match_matrix) - 1):
        current_round = match_matrix[round_index]
        next_round = match_matrix[round_index + 1]

        for bm in current_round:
            match = await session.get(Match, bm.match_id)
            if not (match and match.is_finished and match.winner_id):
                continue

            next_position = (bm.position + 1) // 2
            next_bm = next((m for m in next_round if m.position == next_position), None)
            if not next_bm:
                continue

            next_match = await session.get(Match, next_bm.match_id)
            if bm.position % 2 == 1:
                next_match.athlete1_id = match.winner_id
            else:
                next_match.athlete2_id = match.winner_id


async def regenerate_bracket_matches(
    session: AsyncSession,
    bracket_id: int,
    commit: bool = True,
    skip_first_round: bool = False,
):
    # Удалим все BracketMatch + Match
    await session.execute(
        delete(Match).where(
            Match.id.in_(
                select(BracketMatch.match_id).where(
                    BracketMatch.bracket_id == bracket_id
                )
            )
        )
    )
    await session.execute(
        delete(BracketMatch).where(BracketMatch.bracket_id == bracket_id)
    )

    result = await session.execute(
        select(BracketParticipant)
        .filter_by(bracket_id=bracket_id)
        .order_by(BracketParticipant.seed)
    )
    participants = result.scalars().all()
    athlete_ids = [p.athlete_id for p in participants if p.athlete_id is not None]

    num_players = len(athlete_ids)
    next_power_of_two = 2 ** math.ceil(math.log2(max(num_players, 2)))
    total_rounds = int(math.log2(next_power_of_two))

    match_matrix = [[] for _ in range(total_rounds)]

    if not skip_first_round:
        match_matrix[0] = await generate_first_round(
            session, bracket_id, athlete_ids, total_rounds
        )

    later_rounds = await generate_following_rounds(session, bracket_id, total_rounds)
    for i in range(1, total_rounds):
        match_matrix[i] = later_rounds[i] if i < len(later_rounds) else []

    # Связи next_match
    for round_index in range(len(match_matrix) - 1):
        current_round = match_matrix[round_index]
        next_round = match_matrix[round_index + 1]
        for i, match in enumerate(current_round):
            next_match = next_round[i // 2]
            match.next_match_id = next_match.id
            match.next_slot = 1 if i % 2 == 0 else 2

    await advance_auto_winners(session, match_matrix)

    if commit:
        await session.commit()
    else:
        return match_matrix


async def regenerate_tournament_brackets(session: AsyncSession, tournament_id: int):
    result = await session.execute(
        select(Bracket.id).where(Bracket.tournament_id == tournament_id)
    )
    bracket_ids = result.scalars().all()

    for bracket_id in bracket_ids:
        await regenerate_bracket_matches(session, bracket_id, commit=False)

    await session.flush()
    await session.commit()
