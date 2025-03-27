from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from src.database import get_db
from src.models import Bracket, BracketMatch, BracketParticipant
from src.schemas import BracketMatchResponse, BracketResponse, BracketParticipantSchema

router = APIRouter(prefix="/brackets", tags=["Brackets"])


@router.get("", response_model=List[BracketResponse])
async def get_all_brackets(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Bracket).options(
            selectinload(Bracket.category),
            selectinload(Bracket.participants).selectinload(BracketParticipant.athlete),
        )
    )
    brackets = result.scalars().all()

    return [
        BracketResponse(
            id=bracket.id,
            tournament_id=bracket.tournament_id,
            category=bracket.category.name,
            participants=[
                BracketParticipantSchema(
                    seed=p.seed,
                    first_name=p.athlete.first_name,
                    last_name=p.athlete.last_name,
                )
                for p in sorted(bracket.participants, key=lambda x: x.seed)
                if p.athlete
            ],
        )
        for bracket in brackets
    ]


@router.get("/{bracket_id}", response_model=BracketResponse)
async def get_bracket_by_id(bracket_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Bracket)
        .filter(Bracket.id == bracket_id)
        .options(
            selectinload(Bracket.category),
            selectinload(Bracket.participants).selectinload(BracketParticipant.athlete),
        )
    )
    bracket = result.scalars().first()
    if not bracket:
        raise HTTPException(status_code=404, detail="Bracket not found")

    return BracketResponse(
        id=bracket.id,
        tournament_id=bracket.tournament_id,
        category=bracket.category.name if bracket.category else "Без категории",
        participants=[
            BracketParticipantSchema(
                seed=p.seed,
                first_name=p.athlete.first_name,
                last_name=p.athlete.last_name,
            )
            for p in sorted(bracket.participants, key=lambda x: x.seed)
            if p.athlete
        ],
    )


@router.get("/{bracket_id}/matches", response_model=List[BracketMatchResponse])
async def get_bracket_matches(bracket_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(BracketMatch)
        .where(BracketMatch.bracket_id == bracket_id)
        .options(
            selectinload(BracketMatch.athlete1),
            selectinload(BracketMatch.athlete2),
            selectinload(BracketMatch.winner),
        )
        .order_by(BracketMatch.round_number, BracketMatch.position)
    )
    matches = result.scalars().all()

    response = []
    for match in matches:
        response.append(
            BracketMatchResponse(
                id=match.id,
                round_number=match.round_number,
                position=match.position,
                athlete1=match.athlete1,
                athlete2=match.athlete2,
                winner=match.winner,
                score_athlete1=match.score_athlete1,
                score_athlete2=match.score_athlete2,
                is_finished=match.is_finished,
            )
        )
    return response
