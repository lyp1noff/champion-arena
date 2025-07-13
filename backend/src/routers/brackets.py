from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from src.database import get_db
from src.dependencies.auth import get_current_user
from src.models import (
    Bracket,
    BracketMatch,
    BracketParticipant,
    Match,
    Athlete,
    AthleteCoachLink,
)
from src.schemas import (
    BracketResponse,
    BracketMatchResponse,
    BracketMatchesFull,
    BracketUpdateSchema,
)
from src.services.serialize import (
    serialize_bracket,
    serialize_bracket_match,
    serialize_bracket_matches_full,
)
from src.services.brackets import (
    regenerate_bracket_matches,
    regenerate_round_bracket_matches,
)

router = APIRouter(prefix="/brackets", tags=["Brackets"])


@router.get("", response_model=List[BracketResponse])
async def get_all_brackets(db: AsyncSession = Depends(get_db)):
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
async def get_bracket(bracket_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Bracket)
        .filter_by(id=bracket_id)
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
):
    result = await db.execute(select(Bracket).where(Bracket.id == bracket_id))
    bracket = result.scalars().first()

    if not bracket:
        raise HTTPException(status_code=404, detail="Bracket not found")

    old_type = bracket.type

    for key, value in update_data.model_dump(exclude_unset=True).items():
        setattr(bracket, key, value)

    await db.commit()
    await db.refresh(bracket)

    if update_data.type and update_data.type != old_type:
        await regenerate_matches_endpoint(bracket_id, session=db)

    return bracket


@router.get("/{bracket_id}/matches", response_model=List[BracketMatchResponse])
async def get_bracket_matches(bracket_id: int, db: AsyncSession = Depends(get_db)):
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
    session: AsyncSession = Depends(get_db),
):
    try:
        result = await session.execute(
            select(Bracket.type, Bracket.tournament_id).where(Bracket.id == bracket_id)
        )
        bracket_data = result.first()
        if not bracket_data:
            raise HTTPException(status_code=404, detail="Bracket not found")

        bracket_type, tournament_id = bracket_data
        if bracket_type == "round_robin":
            await regenerate_round_bracket_matches(session, bracket_id, tournament_id)
        elif bracket_type == "single_elimination":
            await regenerate_bracket_matches(session, bracket_id, tournament_id)
        else:
            print(f"Warning! Bracket type: {bracket_type} not supported")
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to regenerate: {str(e)}")
