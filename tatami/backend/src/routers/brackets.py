from champion_domain import compute_main_rounds
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database import get_db
from src.models import Bracket, BracketMatch, Match
from src.schemas import (
    BracketMatchSchema,
    BracketParticipantAddSchema,
    BracketParticipantMoveSchema,
    BracketParticipantSchema,
    BracketParticipantSeedUpdateSchema,
)
from src.services.brackets import (
    add_participant_to_bracket,
    get_bracket_by_external_id,
    list_bracket_participants,
    move_participant_between_brackets,
    remove_participant_from_bracket,
    update_participant_seed,
)
from src.services.outbox import create_bracket_upsert_outbox
from src.transport.mappers import to_bracket_match_schema

router = APIRouter(
    prefix="/brackets",
    tags=["Brackets"],
)


@router.get("/{bracket_id}/matches", response_model=list[BracketMatchSchema])
async def get_bracket_matches(bracket_id: int, db: AsyncSession = Depends(get_db)) -> list[BracketMatchSchema]:
    result = await db.execute(
        select(BracketMatch)
        .join(Bracket, BracketMatch.bracket_id == Bracket.id)
        .where(Bracket.external_id == bracket_id)
        .options(
            selectinload(BracketMatch.match).selectinload(Match.athlete1),
            selectinload(BracketMatch.match).selectinload(Match.athlete2),
        )
        .order_by(BracketMatch.round_number, BracketMatch.position)
    )
    matches = result.scalars().all()
    if not matches:
        raise HTTPException(status_code=404, detail=f"Bracket {bracket_id} not found")

    bracket = await get_bracket_by_external_id(db, bracket_id)
    participants_count = sum(1 for participant in bracket.participants if participant.athlete_id is not None)
    main_rounds = int(compute_main_rounds(participants_count))

    return [to_bracket_match_schema(m, main_rounds=main_rounds) for m in matches]


@router.get("/{bracket_id}/participants", response_model=list[BracketParticipantSchema])
async def get_bracket_participants(
    bracket_id: int,
    db: AsyncSession = Depends(get_db),
) -> list[BracketParticipantSchema]:
    participants = await list_bracket_participants(db, bracket_id)
    return [BracketParticipantSchema.model_validate(participant) for participant in participants]


@router.post("/{bracket_id}/participants", response_model=BracketParticipantSchema)
async def add_bracket_participant(
    bracket_id: int,
    payload: BracketParticipantAddSchema,
    db: AsyncSession = Depends(get_db),
) -> BracketParticipantSchema:
    participant = await add_participant_to_bracket(
        db,
        bracket_external_id=bracket_id,
        athlete_external_id=payload.athlete_external_id,
        seed=payload.seed,
    )
    return BracketParticipantSchema.model_validate(participant)


@router.delete("/{bracket_id}/participants/{participant_id}", response_model=dict[str, str])
async def delete_bracket_participant(
    bracket_id: int,
    participant_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    await remove_participant_from_bracket(
        db,
        bracket_external_id=bracket_id,
        participant_id=participant_id,
    )
    return {"status": "ok"}


@router.patch("/{bracket_id}/participants/{participant_id}", response_model=BracketParticipantSchema)
async def patch_bracket_participant(
    bracket_id: int,
    participant_id: int,
    payload: BracketParticipantSeedUpdateSchema,
    db: AsyncSession = Depends(get_db),
) -> BracketParticipantSchema:
    participant = await update_participant_seed(
        db,
        bracket_external_id=bracket_id,
        participant_id=participant_id,
        seed=payload.seed,
    )
    return BracketParticipantSchema.model_validate(participant)


@router.post("/participants/move", response_model=dict[str, str])
async def move_bracket_participant(
    payload: BracketParticipantMoveSchema,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    await move_participant_between_brackets(
        db,
        participant_id=payload.participant_id,
        target_bracket_external_id=payload.target_bracket_id,
        target_seed=payload.target_seed,
    )
    return {"status": "ok"}


@router.post("/{bracket_id}/sync-bracket")
async def sync_bracket_upsert(bracket_id: int, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    bracket_result = await db.execute(select(Bracket).where(Bracket.external_id == bracket_id))
    bracket = bracket_result.scalar_one_or_none()
    if bracket is None:
        raise HTTPException(status_code=404, detail=f"Bracket {bracket_id} not found")

    if bracket.state in {"running", "finished"}:
        raise HTTPException(status_code=409, detail="Running or finished bracket is structurally immutable")

    await create_bracket_upsert_outbox(bracket, db)
    await db.commit()

    return {"status": "ok"}


@router.post("/{bracket_id}/unlock")
async def unlock_bracket(
    bracket_id: int,
    publish: bool = Query(default=False, description="Enqueue bracket.upsert after unlock"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str | int]:
    bracket_result = await db.execute(select(Bracket).where(Bracket.external_id == bracket_id))
    bracket = bracket_result.scalar_one_or_none()
    if bracket is None:
        raise HTTPException(status_code=404, detail=f"Bracket {bracket_id} not found")

    previous_state = bracket.state
    bracket.state = "draft"
    if bracket.status in {"started", "finished"}:
        bracket.status = "pending"
    bracket.version = max(1, bracket.version + 1)

    if publish:
        await create_bracket_upsert_outbox(bracket, db)

    await db.commit()

    return {
        "status": "ok",
        "bracket_id": bracket_id,
        "previous_state": previous_state,
        "state": bracket.state,
        "version": bracket.version,
    }
