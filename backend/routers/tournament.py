from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from schemas import TournamentResponse, TournamentCreate
from database import get_db
from crud import get_tournament, create_tournament, get_tournaments

router = APIRouter()

@router.get("/tournaments", response_model=list[TournamentResponse])
async def get_all_tournaments(db: AsyncSession = Depends(get_db)):
    return await get_tournaments(db=db)


@router.get("/tournament/{id}", response_model=TournamentResponse)
async def get_tournament_by_id(id: int, db: AsyncSession = Depends(get_db)):
    return await get_tournament(db=db, id=id)

@router.post("/tournament", response_model=TournamentResponse)
async def create_new_tournament(tournament: TournamentCreate, db: AsyncSession = Depends(get_db)):
    return await create_tournament(db=db, tournament = tournament)
