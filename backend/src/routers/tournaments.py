from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import asc, desc, func, select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies.auth import get_current_user
from src.models import Bracket, BracketMatch, BracketParticipant, Tournament
from src.schemas import (
    BracketMatchGroup,
    BracketMatchResponse,
    BracketParticipantSchema,
    BracketResponse,
    TournamentResponse,
    TournamentCreate,
    PaginatedTournamentResponse,
    TournamentUpdate,
)
from src.database import get_db
from src.services.brackets import regenerate_tournament_brackets

router = APIRouter(
    prefix="/tournaments",
    tags=["Tournaments"],
)


@router.get("", response_model=PaginatedTournamentResponse)
async def get_tournaments(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    order_by: str = Query("id"),
    order: str = Query("asc"),
    search: str = Query(None),
    db: AsyncSession = Depends(get_db),
):
    valid_order_fields = {"id", "name", "location", "start_date", "end_date"}
    order_by = order_by if order_by in valid_order_fields else "id"

    order_column = (
        desc(getattr(Tournament, order_by))
        if order.lower() == "desc"
        else asc(getattr(Tournament, order_by))
    )
    offset = (page - 1) * limit

    filters = [Tournament.name.ilike(f"%{search}%")] if search else []

    total = await db.scalar(select(func.count(Tournament.id)).where(*filters))

    result = await db.execute(
        select(Tournament)
        .where(*filters)
        .order_by(order_column)
        .offset(offset)
        .limit(limit)
    )

    return {
        "data": result.scalars().all(),
        "total": total or 0,
        "page": page,
        "limit": limit,
    }


@router.get("/{id}", response_model=TournamentResponse)
async def get_tournament(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tournament).filter(Tournament.id == id))
    tournament = result.scalars().first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    return tournament


@router.post(
    "", response_model=TournamentResponse, dependencies=[Depends(get_current_user)]
)
async def create_tournament(
    tournament: TournamentCreate, db: AsyncSession = Depends(get_db)
):
    try:
        new_tournament = Tournament(**tournament.model_dump())
        db.add(new_tournament)
        await db.commit()
        await db.refresh(new_tournament)
        return new_tournament
    except IntegrityError:
        raise HTTPException(
            status_code=400, detail="Tournament with these details already exists"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put(
    "/{id}", response_model=TournamentResponse, dependencies=[Depends(get_current_user)]
)
async def update_tournament(
    id: int, tournament_update: TournamentUpdate, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Tournament).filter(Tournament.id == id))
    tournament = result.scalars().first()

    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    for key, value in tournament_update.model_dump(exclude_unset=True).items():
        setattr(tournament, key, value)

    await db.commit()
    await db.refresh(tournament)

    return tournament


@router.delete("/{id}", dependencies=[Depends(get_current_user)], status_code=204)
async def delete_tournament(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tournament).filter(Tournament.id == id))
    tournament = result.scalars().first()

    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    await db.delete(tournament)
    await db.commit()


# @router.get("/{tournament_id}/brackets", response_model=List[BracketBase])
# async def get_brackets(tournament_id: int, db: AsyncSession = Depends(get_db)):
#     result = await db.execute(
#         select(Bracket)
#         .filter_by(tournament_id=tournament_id)
#         .order_by(Bracket.id)
#         .options(
#             selectinload(Bracket.category),
#             selectinload(Bracket.participants).selectinload(BracketParticipant.athlete),
#         )
#     )
#     brackets = result.scalars().all()

#     brackets_data = []

#     for bracket in brackets:
#         if not bracket.category:
#             continue

#         sorted_participants = sorted(bracket.participants, key=lambda x: x.seed)

#         participant_list = [
#             {
#                 "seed": p.seed,
#                 "last_name": p.athlete.last_name,
#                 "first_name": p.athlete.first_name,
#             }
#             for p in sorted_participants
#             if p.athlete
#         ]

#         brackets_data.append(
#             {"category": bracket.category.name, "participants": participant_list}
#         )

#     return brackets_data


@router.get("/{tournament_id}/brackets", response_model=List[BracketResponse])
async def get_all_brackets(tournament_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Bracket)
        .filter_by(tournament_id=tournament_id)
        .options(
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


@router.get("/{tournament_id}/matches", response_model=List[BracketMatchGroup])
async def get_all_matches_for_tournament(
    tournament_id: int, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Bracket)
        .filter(Bracket.tournament_id == tournament_id)
        .options(
            selectinload(Bracket.category),
            selectinload(Bracket.matches).selectinload(BracketMatch.athlete1),
            selectinload(Bracket.matches).selectinload(BracketMatch.athlete2),
            selectinload(Bracket.matches).selectinload(BracketMatch.winner),
        )
    )
    brackets = result.scalars().all()

    response = []
    for bracket in brackets:
        matches = []
        for match in sorted(
            bracket.matches, key=lambda m: (m.round_number, m.position)
        ):
            matches.append(
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
        response.append(
            BracketMatchGroup(
                bracket_id=bracket.id,
                category=bracket.category.name if bracket.category else "Без категории",
                matches=matches,
            )
        )

    return response


@router.post("/{tournament_id}/regenerate", dependencies=[Depends(get_current_user)])
async def regenerate_tournament(
    tournament_id: int, session: AsyncSession = Depends(get_db)
):
    try:
        await regenerate_tournament_brackets(session, tournament_id)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
