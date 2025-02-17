from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas import TournamentResponse, TournamentCreate
from src.database import get_db
from src.tournaments.crud import (
    create_tournament as crud_create_tournament,
    get_all_tournaments as crud_get_all_tournaments,
    get_tournament_by_id as crud_get_tournament_by_id,
)

router = APIRouter()

@router.get("/tournaments", response_model=list[TournamentResponse])
async def get_tournaments(db: AsyncSession = Depends(get_db)):
    return await crud_get_all_tournaments(db=db)


@router.get("/tournaments/{id}", response_model=TournamentResponse)
async def get_tournament(id: int, db: AsyncSession = Depends(get_db)):
    return await crud_get_tournament_by_id(db=db, id=id)

@router.post("/tournaments", response_model=TournamentResponse)
async def create_tournament(tournament: TournamentCreate, db: AsyncSession = Depends(get_db)):
    return await crud_create_tournament(db=db, tournament = tournament)
