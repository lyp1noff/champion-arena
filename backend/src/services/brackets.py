import math
from datetime import UTC, datetime
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from src.logger import logger
from src.models import (
    Athlete,
    AthleteCoachLink,
    Bracket,
    BracketMatch,
    BracketParticipant,
    BracketStatus,
    BracketType,
    Category,
    Match,
    MatchStatus,
    Tournament,
)
from src.schemas import (
    BracketCreateSchema,
    BracketDeleteRequest,
    BracketUpdateSchema,
    ParticipantMoveSchema,
    ParticipantReorderSchema,
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

    await db.flush()
    return len(participants) + 1


async def get_all_brackets(db: AsyncSession) -> list[Bracket]:
    result = await db.execute(
        select(Bracket).options(
            selectinload(Bracket.category),
            selectinload(Bracket.participants)
            .selectinload(BracketParticipant.athlete)
            .selectinload(Athlete.coach_links)
            .joinedload(AthleteCoachLink.coach),
        )
    )
    return list(result.scalars().all())


async def get_bracket(db: AsyncSession, bracket_id: int) -> Bracket:
    result = await db.execute(
        select(Bracket)
        .where(Bracket.id == bracket_id)
        .options(
            selectinload(Bracket.category),
            selectinload(Bracket.participants)
            .selectinload(BracketParticipant.athlete)
            .selectinload(Athlete.coach_links)
            .joinedload(AthleteCoachLink.coach),
        )
    )
    bracket = result.scalar_one_or_none()
    if not bracket:
        raise HTTPException(status_code=404, detail="Bracket not found")
    return bracket


async def get_bracket_matches(db: AsyncSession, bracket_id: int) -> list[BracketMatch]:
    result = await db.execute(
        select(BracketMatch)
        .filter_by(bracket_id=bracket_id)
        .options(
            selectinload(BracketMatch.match)
            .selectinload(Match.athlete1)
            .selectinload(Athlete.coach_links)
            .joinedload(AthleteCoachLink.coach),
            selectinload(BracketMatch.match)
            .selectinload(Match.athlete2)
            .selectinload(Athlete.coach_links)
            .joinedload(AthleteCoachLink.coach),
            selectinload(BracketMatch.match)
            .selectinload(Match.winner)
            .selectinload(Athlete.coach_links)
            .joinedload(AthleteCoachLink.coach),
        )
        .order_by(BracketMatch.round_number, BracketMatch.position)
    )
    return list(result.scalars().all())


async def update_bracket(db: AsyncSession, bracket_id: int, update_data: BracketUpdateSchema) -> tuple[Bracket, bool]:
    result = await db.execute(select(Bracket).where(Bracket.id == bracket_id).options(selectinload(Bracket.category)))
    bracket = result.scalars().first()
    if not bracket:
        raise HTTPException(status_code=404, detail="Bracket not found")

    old_type = bracket.type
    new_category_id = update_data.category_id if update_data.category_id is not None else bracket.category_id
    new_group_id = update_data.group_id if update_data.group_id is not None else bracket.group_id
    new_tournament_id = bracket.tournament_id
    if update_data.category_id is not None or update_data.group_id is not None:
        existing = await db.execute(
            select(Bracket).where(
                Bracket.tournament_id == new_tournament_id,
                Bracket.category_id == new_category_id,
                Bracket.group_id == new_group_id,
                Bracket.id != bracket_id,
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail="Bracket already exists for this category and group in this tournament",
            )

    for key, value in update_data.model_dump(exclude_unset=True).items():
        setattr(bracket, key, value)

    await db.commit()
    await db.refresh(bracket)
    return bracket, bool(update_data.type and update_data.type != old_type)


async def move_participant(db: AsyncSession, move_data: ParticipantMoveSchema) -> None:
    participant: BracketParticipant | None = await db.get(BracketParticipant, move_data.participant_id)
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")

    if participant.bracket_id != move_data.from_bracket_id:
        raise HTTPException(status_code=400, detail="Participant not in source bracket")

    existing = await db.execute(
        select(BracketParticipant).where(
            BracketParticipant.bracket_id == move_data.to_bracket_id,
            BracketParticipant.athlete_id == participant.athlete_id,
        )
    )
    if existing.scalar():
        raise HTTPException(status_code=400, detail="Athlete already in target bracket")

    await db.delete(participant)
    await db.flush()

    new_seed = await reorder_seeds_and_get_next(db, move_data.to_bracket_id)
    new_participant = BracketParticipant(
        bracket_id=move_data.to_bracket_id,
        athlete_id=participant.athlete_id,
        seed=new_seed,
    )
    db.add(new_participant)
    await db.commit()


async def reorder_participants(db: AsyncSession, reorder_data: ParticipantReorderSchema) -> None:
    for upd in reorder_data.participant_updates:
        await db.execute(
            update(BracketParticipant)
            .where(
                BracketParticipant.bracket_id == reorder_data.bracket_id,
                BracketParticipant.id == upd["participant_id"],
            )
            .values(seed=upd["new_seed"])
        )
    await db.commit()


async def create_bracket(db: AsyncSession, bracket_data: BracketCreateSchema) -> Bracket:
    tournament = await db.get(Tournament, bracket_data.tournament_id)
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    category = await db.get(Category, bracket_data.category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    existing_bracket = await db.execute(
        select(Bracket).where(
            Bracket.tournament_id == bracket_data.tournament_id,
            Bracket.category_id == bracket_data.category_id,
            Bracket.group_id == bracket_data.group_id,
        )
    )
    if existing_bracket.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Bracket already exists for this category and group")

    new_bracket = Bracket(
        tournament_id=bracket_data.tournament_id,
        category_id=bracket_data.category_id,
        group_id=bracket_data.group_id,
        type=bracket_data.type,
    )

    db.add(new_bracket)
    await db.commit()

    result = await db.execute(
        select(Bracket)
        .options(
            joinedload(Bracket.category),
            joinedload(Bracket.participants)
            .joinedload(BracketParticipant.athlete)
            .joinedload(Athlete.coach_links)
            .joinedload(AthleteCoachLink.coach),
        )
        .where(Bracket.id == new_bracket.id)
    )
    return result.unique().scalar_one()


async def delete_bracket(db: AsyncSession, bracket_id: int, data: BracketDeleteRequest) -> None:
    bracket = await db.get(Bracket, bracket_id)
    if not bracket:
        raise HTTPException(status_code=404, detail="Bracket not found")

    result = await db.execute(select(BracketParticipant).where(BracketParticipant.bracket_id == bracket_id))
    participants = result.scalars().all()

    if participants and not data.target_bracket_id:
        raise HTTPException(status_code=400, detail="Bracket has participants; target bracket required")

    if data.target_bracket_id:
        for p in participants:
            dup = await db.execute(
                select(BracketParticipant).where(
                    BracketParticipant.bracket_id == data.target_bracket_id,
                    BracketParticipant.athlete_id == p.athlete_id,
                )
            )
            if dup.scalar():
                raise HTTPException(
                    status_code=400,
                    detail=f"Athlete {p.id} already in target bracket",
                )

            new_seed = await reorder_seeds_and_get_next(db, data.target_bracket_id)
            p.bracket_id = data.target_bracket_id
            p.seed = new_seed

    await db.delete(bracket)
    await db.commit()


async def update_bracket_status(db: AsyncSession, bracket_id: int, status: str) -> Bracket:
    result = await db.execute(
        select(Bracket)
        .where(Bracket.id == bracket_id)
        .options(
            selectinload(Bracket.category),
            selectinload(Bracket.participants)
            .selectinload(BracketParticipant.athlete)
            .selectinload(Athlete.coach_links)
            .joinedload(AthleteCoachLink.coach),
        )
    )
    bracket = result.scalar_one_or_none()
    if not bracket:
        raise HTTPException(404, "Bracket not found")
    if status not in [s.value for s in BracketStatus]:
        raise HTTPException(400, f"Invalid status: {status}")

    bracket.status = status
    await db.commit()
    return bracket


async def start_bracket(db: AsyncSession, bracket_id: int) -> None:
    bracket = await db.get(Bracket, bracket_id)
    if not bracket:
        raise HTTPException(404, "Bracket not found")
    if bracket.status != BracketStatus.PENDING.value:
        raise HTTPException(400, "Bracket already started or finished")

    bracket.status = BracketStatus.STARTED.value
    await db.commit()
