from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload, selectinload

from src.database import get_db
from src.dependencies.auth import get_current_user
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
    Tournament,
)
from src.schemas import (
    BracketCreateSchema,
    BracketDeleteRequest,
    BracketInfoResponse,
    BracketMatchResponse,
    BracketResponse,
    BracketUpdateSchema,
    ParticipantMoveSchema,
    ParticipantReorderSchema,
)
from src.services.brackets import (
    regenerate_bracket_matches,
    regenerate_round_bracket_matches,
    reorder_seeds_and_get_next,
)
from src.services.serialize import serialize_bracket, serialize_bracket_info, serialize_bracket_match

router = APIRouter(prefix="/brackets", tags=["Brackets"])


@router.get("", response_model=list[BracketResponse])
async def get_all_brackets(db: AsyncSession = Depends(get_db)) -> list[BracketResponse]:
    result = await db.execute(
        select(Bracket).options(
            selectinload(Bracket.category),
            selectinload(Bracket.participants)
            .selectinload(BracketParticipant.athlete)
            .selectinload(Athlete.coach_links)
            .joinedload(AthleteCoachLink.coach),
        )
    )
    brackets = result.scalars().all()
    return [serialize_bracket(b) for b in brackets]


@router.get("/{bracket_id}", response_model=BracketResponse)
async def get_bracket(bracket_id: int, db: AsyncSession = Depends(get_db)) -> BracketResponse:
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

    return serialize_bracket(bracket)


@router.put("/{bracket_id}", dependencies=[Depends(get_current_user)])
async def update_bracket(
    bracket_id: int,
    update_data: BracketUpdateSchema,
    db: AsyncSession = Depends(get_db),
) -> BracketInfoResponse:
    result = await db.execute(select(Bracket).where(Bracket.id == bracket_id).options(selectinload(Bracket.category)))
    bracket = result.scalars().first()

    if not bracket:
        raise HTTPException(status_code=404, detail="Bracket not found")

    old_type = bracket.type

    # TODO: Prbly remove uniqueness constraint
    # If category_id, group_id, or tournament_id are being updated, check uniqueness constraint
    new_category_id = update_data.category_id if update_data.category_id is not None else bracket.category_id
    new_group_id = update_data.group_id if update_data.group_id is not None else bracket.group_id
    new_tournament_id = bracket.tournament_id  # tournament_id is not updatable, but included for completeness
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

    if update_data.type and update_data.type != old_type:
        await regenerate_matches_endpoint(bracket_id, db)

    return serialize_bracket_info(bracket)


@router.get("/{bracket_id}/matches", response_model=list[BracketMatchResponse])
async def get_bracket_matches(bracket_id: int, db: AsyncSession = Depends(get_db)) -> list[BracketMatchResponse]:
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
    matches = result.scalars().all()
    return [serialize_bracket_match(match) for match in matches]


@router.post("/{bracket_id}/regenerate", dependencies=[Depends(get_current_user)])
async def regenerate_matches_endpoint(
    bracket_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    try:
        result = await db.execute(select(Bracket.type, Bracket.tournament_id).where(Bracket.id == bracket_id))
        bracket_data = result.first()
        if not bracket_data:
            raise HTTPException(status_code=404, detail="Bracket not found")

        bracket_type, tournament_id = bracket_data
        if bracket_type == BracketType.ROUND_ROBIN.value:
            await regenerate_round_bracket_matches(db, bracket_id, tournament_id)
        elif bracket_type == BracketType.SINGLE_ELIMINATION.value:
            await regenerate_bracket_matches(db, bracket_id, tournament_id)
        else:
            print(f"Warning! Bracket type: {bracket_type} not supported")
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to regenerate: {str(e)}")


@router.post("/participants/move", dependencies=[Depends(get_current_user)])
async def move_participant(
    move_data: ParticipantMoveSchema,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
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
    await db.flush()  # Release id

    new_seed = await reorder_seeds_and_get_next(db, move_data.to_bracket_id)

    new_participant = BracketParticipant(
        bracket_id=move_data.to_bracket_id,
        athlete_id=participant.athlete_id,
        seed=new_seed,
    )
    db.add(new_participant)

    await db.commit()

    # Regenerate matches for both brackets
    await regenerate_matches_endpoint(move_data.from_bracket_id, db)
    await regenerate_matches_endpoint(move_data.to_bracket_id, db)

    return {"status": "ok"}


@router.post("/participants/reorder", dependencies=[Depends(get_current_user)])
async def reorder_participants(
    reorder_data: ParticipantReorderSchema,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
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
    return {"status": "ok"}


@router.post("/create", dependencies=[Depends(get_current_user)])
async def create_bracket(
    bracket_data: BracketCreateSchema,
    db: AsyncSession = Depends(get_db),
) -> BracketResponse:
    # Check if tournament exists
    tournament = await db.get(Tournament, bracket_data.tournament_id)
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    # Check if category exists
    category = await db.get(Category, bracket_data.category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Check if bracket already exists for this tournament/category/group combination
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
        start_time=bracket_data.start_time,
        tatami=bracket_data.tatami,
    )

    db.add(new_bracket)
    await db.commit()
    await db.refresh(new_bracket)

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
    bracket_full = result.unique().scalar_one()

    return serialize_bracket(bracket_full)


@router.post("/{bracket_id}/delete", dependencies=[Depends(get_current_user)])
async def delete_bracket(
    bracket_id: int,
    data: BracketDeleteRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
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

    if data.target_bracket_id:
        await regenerate_matches_endpoint(data.target_bracket_id, db)

    return {"status": "ok"}


@router.get("/{id}/status")
async def get_bracket_status(id: int, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    bracket = await db.get(Bracket, id)
    if not bracket:
        raise HTTPException(404, "Bracket not found")
    return {"status": bracket.status}


@router.patch("/{id}/status", dependencies=[Depends(get_current_user)])
async def update_bracket_status(
    id: int,
    status: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
) -> BracketResponse:
    result = await db.execute(
        select(Bracket)
        .where(Bracket.id == id)
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
    await db.refresh(bracket)
    return serialize_bracket(bracket)


@router.post("/{id}/start", dependencies=[Depends(get_current_user)])
async def start_bracket(id: int, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    bracket = await db.get(Bracket, id)
    if not bracket:
        raise HTTPException(404, "Bracket not found")
    if bracket.status != BracketStatus.PENDING.value:
        raise HTTPException(400, "Bracket already started or finished")

    bracket.status = BracketStatus.STARTED.value
    await db.commit()
    return {"status": "ok"}
