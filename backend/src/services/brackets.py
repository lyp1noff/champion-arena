from datetime import UTC, datetime
from typing import Optional

from champion_domain import (
    IMMUTABLE_BRACKET_STATES,
    SeededParticipant,
    bump_bracket_version,
    derive_bracket_state_from_status,
    is_bracket_structurally_mutable,
    plan_bracket_matches,
)
from champion_domain.use_cases import PlannedMatch
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
    MatchStage,
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


async def _ensure_bracket_editable(db: AsyncSession, bracket_id: int) -> Bracket:
    bracket = await db.get(Bracket, bracket_id)
    if bracket is None:
        raise HTTPException(status_code=404, detail="Bracket not found")
    if not is_bracket_structurally_mutable(bracket.state):
        raise HTTPException(status_code=409, detail="Running or finished bracket is structurally immutable")
    return bracket


async def _reset_and_clear_bracket_structure(db: AsyncSession, bracket_id: int) -> Bracket:
    bracket = await _ensure_bracket_editable(db, bracket_id)
    bracket.place_1_id = None
    bracket.place_2_id = None
    bracket.place_3_a_id = None
    bracket.place_3_b_id = None
    bump_bracket_version(bracket)

    await db.execute(
        delete(Match).where(Match.id.in_(select(BracketMatch.match_id).where(BracketMatch.bracket_id == bracket_id)))
    )
    await db.execute(delete(BracketMatch).where(BracketMatch.bracket_id == bracket_id))
    return bracket


async def generate_all_rounds(
    db: AsyncSession, bracket_id: int, planned_matches: list[PlannedMatch]
) -> list[BracketMatch]:
    created: list[BracketMatch] = []

    for planned in planned_matches:
        is_bye_win = planned.status == MatchStatus.FINISHED.value and planned.winner_id is not None
        match = Match(
            athlete1_id=planned.athlete1_id,
            athlete2_id=planned.athlete2_id,
            winner_id=planned.winner_id,
            round_type=planned.round_type,
            stage=MatchStage.MAIN.value,
            status=planned.status,
            ended_at=datetime.now(UTC) if is_bye_win else None,
        )
        db.add(match)
        await db.flush()

        bracket_match = BracketMatch(
            bracket_id=bracket_id,
            round_number=planned.round_number,
            position=planned.position,
            match_id=match.id,
            next_slot=planned.next_slot,
        )
        db.add(bracket_match)
        created.append(bracket_match)

    return created


async def regenerate_bracket_matches(
    db: AsyncSession, bracket_id: int, tournament_id: int, commit: bool = True
) -> None:
    await _reset_and_clear_bracket_structure(db, bracket_id)

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

    planned_matches = plan_bracket_matches(
        bracket_type=BracketType.SINGLE_ELIMINATION.value,
        participants=[
            SeededParticipant(seed=participant.seed, athlete_id=participant.athlete_id) for participant in participants
        ],
    )
    await generate_all_rounds(db, bracket_id, planned_matches)

    if commit:
        tournament = await db.get(Tournament, tournament_id)
        if tournament is not None:
            tournament.export_last_updated_at = datetime.now(UTC)
        await db.commit()
    return None


async def regenerate_round_bracket_matches(
    db: AsyncSession, bracket_id: int, tournament_id: int, commit: bool = True
) -> Optional[list[BracketMatch]]:
    await _reset_and_clear_bracket_structure(db, bracket_id)

    result = await db.execute(
        select(BracketParticipant).filter_by(bracket_id=bracket_id).order_by(BracketParticipant.seed)
    )
    participants = result.scalars().all()
    matches: list[BracketMatch] = []
    if len(participants) < 2:
        if commit:
            tournament = await db.get(Tournament, tournament_id)
            if tournament is not None:
                tournament.export_last_updated_at = datetime.now(UTC)
            await db.commit()
        return None if commit else matches

    planned_matches = plan_bracket_matches(
        bracket_type=BracketType.ROUND_ROBIN.value,
        participants=[
            SeededParticipant(seed=participant.seed, athlete_id=participant.athlete_id) for participant in participants
        ],
    )
    matches.extend(await generate_all_rounds(db, bracket_id, planned_matches))

    if commit:
        tournament = await db.get(Tournament, tournament_id)
        if tournament is not None:
            tournament.export_last_updated_at = datetime.now(UTC)
        await db.commit()
        return None
    else:
        return matches


async def regenerate_tournament_brackets(db: AsyncSession, tournament_id: int) -> None:
    result = await db.execute(
        select(Bracket.id, Bracket.type, Bracket.state).where(Bracket.tournament_id == tournament_id)
    )
    brackets = result.all()

    for bracket_id, bracket_type, state in brackets:
        if state in IMMUTABLE_BRACKET_STATES:
            raise HTTPException(status_code=409, detail=f"Bracket {bracket_id} is immutable")
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
            selectinload(Bracket.place_1_athlete).selectinload(Athlete.coach_links).joinedload(AthleteCoachLink.coach),
            selectinload(Bracket.place_2_athlete).selectinload(Athlete.coach_links).joinedload(AthleteCoachLink.coach),
            selectinload(Bracket.place_3_a_athlete)
            .selectinload(Athlete.coach_links)
            .joinedload(AthleteCoachLink.coach),
            selectinload(Bracket.place_3_b_athlete)
            .selectinload(Athlete.coach_links)
            .joinedload(AthleteCoachLink.coach),
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
            selectinload(Bracket.place_1_athlete).selectinload(Athlete.coach_links).joinedload(AthleteCoachLink.coach),
            selectinload(Bracket.place_2_athlete).selectinload(Athlete.coach_links).joinedload(AthleteCoachLink.coach),
            selectinload(Bracket.place_3_a_athlete)
            .selectinload(Athlete.coach_links)
            .joinedload(AthleteCoachLink.coach),
            selectinload(Bracket.place_3_b_athlete)
            .selectinload(Athlete.coach_links)
            .joinedload(AthleteCoachLink.coach),
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
    result = await db.execute(
        select(Bracket)
        .where(Bracket.id == bracket_id)
        .options(
            selectinload(Bracket.category),
            selectinload(Bracket.place_1_athlete).selectinload(Athlete.coach_links).joinedload(AthleteCoachLink.coach),
            selectinload(Bracket.place_2_athlete).selectinload(Athlete.coach_links).joinedload(AthleteCoachLink.coach),
            selectinload(Bracket.place_3_a_athlete)
            .selectinload(Athlete.coach_links)
            .joinedload(AthleteCoachLink.coach),
            selectinload(Bracket.place_3_b_athlete)
            .selectinload(Athlete.coach_links)
            .joinedload(AthleteCoachLink.coach),
        )
    )
    bracket = result.scalars().first()
    if not bracket:
        raise HTTPException(status_code=404, detail="Bracket not found")
    if bracket.state in IMMUTABLE_BRACKET_STATES:
        raise HTTPException(status_code=409, detail="Running or finished bracket is structurally immutable")

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
    if update_data.model_dump(exclude_unset=True):
        bump_bracket_version(bracket)

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

    from_bracket = await _ensure_bracket_editable(db, move_data.from_bracket_id)
    to_bracket = await _ensure_bracket_editable(db, move_data.to_bracket_id)

    await db.delete(participant)
    await db.flush()

    new_seed = await reorder_seeds_and_get_next(db, move_data.to_bracket_id)
    new_participant = BracketParticipant(
        bracket_id=move_data.to_bracket_id,
        athlete_id=participant.athlete_id,
        seed=new_seed,
    )
    db.add(new_participant)
    bump_bracket_version(from_bracket)
    bump_bracket_version(to_bracket)
    await db.commit()


async def reorder_participants(db: AsyncSession, reorder_data: ParticipantReorderSchema) -> None:
    bracket = await _ensure_bracket_editable(db, reorder_data.bracket_id)
    for upd in reorder_data.participant_updates:
        await db.execute(
            update(BracketParticipant)
            .where(
                BracketParticipant.bracket_id == reorder_data.bracket_id,
                BracketParticipant.id == upd["participant_id"],
            )
            .values(seed=upd["new_seed"])
        )
    bump_bracket_version(bracket)
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
            joinedload(Bracket.place_1_athlete).joinedload(Athlete.coach_links).joinedload(AthleteCoachLink.coach),
            joinedload(Bracket.place_2_athlete).joinedload(Athlete.coach_links).joinedload(AthleteCoachLink.coach),
            joinedload(Bracket.place_3_a_athlete).joinedload(Athlete.coach_links).joinedload(AthleteCoachLink.coach),
            joinedload(Bracket.place_3_b_athlete).joinedload(Athlete.coach_links).joinedload(AthleteCoachLink.coach),
            joinedload(Bracket.participants)
            .joinedload(BracketParticipant.athlete)
            .joinedload(Athlete.coach_links)
            .joinedload(AthleteCoachLink.coach),
        )
        .where(Bracket.id == new_bracket.id)
    )
    return result.unique().scalar_one()


async def delete_bracket(db: AsyncSession, bracket_id: int, data: BracketDeleteRequest) -> None:
    bracket = await _ensure_bracket_editable(db, bracket_id)

    result = await db.execute(select(BracketParticipant).where(BracketParticipant.bracket_id == bracket_id))
    participants = result.scalars().all()

    if participants and not data.target_bracket_id:
        raise HTTPException(status_code=400, detail="Bracket has participants; target bracket required")

    if data.target_bracket_id:
        target_bracket = await _ensure_bracket_editable(db, data.target_bracket_id)
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
        bump_bracket_version(target_bracket)

    await db.delete(bracket)
    await db.commit()


async def update_bracket_status(db: AsyncSession, bracket_id: int, status: str) -> Bracket:
    result = await db.execute(
        select(Bracket)
        .where(Bracket.id == bracket_id)
        .options(
            selectinload(Bracket.category),
            selectinload(Bracket.place_1_athlete).selectinload(Athlete.coach_links).joinedload(AthleteCoachLink.coach),
            selectinload(Bracket.place_2_athlete).selectinload(Athlete.coach_links).joinedload(AthleteCoachLink.coach),
            selectinload(Bracket.place_3_a_athlete)
            .selectinload(Athlete.coach_links)
            .joinedload(AthleteCoachLink.coach),
            selectinload(Bracket.place_3_b_athlete)
            .selectinload(Athlete.coach_links)
            .joinedload(AthleteCoachLink.coach),
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

    if bracket.status != status:
        bump_bracket_version(bracket)
    bracket.status = status
    bracket.state = derive_bracket_state_from_status(status, bracket.state)
    await db.commit()
    return bracket


async def start_bracket(db: AsyncSession, bracket_id: int) -> None:
    bracket = await db.get(Bracket, bracket_id)
    if not bracket:
        raise HTTPException(404, "Bracket not found")
    if bracket.status != BracketStatus.PENDING.value:
        raise HTTPException(400, "Bracket already started or finished")

    bracket.status = BracketStatus.STARTED.value
    bracket.state = derive_bracket_state_from_status(bracket.status, bracket.state)
    bump_bracket_version(bracket)
    await db.commit()
