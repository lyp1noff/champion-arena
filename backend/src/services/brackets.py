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


async def regenerate_bracket_matches(
    session: AsyncSession,
    bracket_id: int,
    commit: bool = True,
):
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
    pairs = distribute_byes_safely(athlete_ids)

    # 1-й раунд
    for position, (a1, a2) in enumerate(pairs, start=1):
        match = Match(
            athlete1_id=a1, athlete2_id=a2, round_type=get_round_type(0, total_rounds)
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
        match_matrix[0].append(bracket_match)

    # Следующие раунды
    for round_num in range(2, total_rounds + 1):
        num_matches = 2 ** (total_rounds - round_num)
        for pos in range(1, num_matches + 1):
            match = Match(
                round_type=get_round_type(round_num - 1, total_rounds),
            )
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

    await session.flush()

    # Связи next_match
    for round_index in range(len(match_matrix) - 1):
        current_round = match_matrix[round_index]
        next_round = match_matrix[round_index + 1]

        for i, match in enumerate(current_round):
            next_match = next_round[i // 2]
            match.next_match_id = next_match.id
            match.next_slot = 1 if i % 2 == 0 else 2

    # Продвижение автопобедителей
    for round_index in range(len(match_matrix) - 1):
        for bm in match_matrix[round_index]:
            match = await session.get(Match, bm.match_id)
            if (
                match.is_finished
                and match.winner_id
                and bm.next_match_id
                and bm.next_slot
            ):
                next_bm = next(
                    (
                        m
                        for m in match_matrix[round_index + 1]
                        if m.id == bm.next_match_id
                    ),
                    None,
                )
                if next_bm:
                    next_match = await session.get(Match, next_bm.match_id)
                    if bm.next_slot == 1:
                        next_match.athlete1_id = match.winner_id
                    else:
                        next_match.athlete2_id = match.winner_id

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
