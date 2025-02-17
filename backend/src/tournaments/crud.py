from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException
from src.database import get_db
from src.models import Tournament
from src.schemas import TournamentCreate


async def get_all_tournaments(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tournament))
    return result.scalars().all()


async def get_tournament_by_id(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tournament).filter(Tournament.id == id))
    tournament = result.scalars().first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    return tournament


async def create_tournament(tournament: TournamentCreate, db: AsyncSession = Depends(get_db)):
    new_tournament = Tournament(**tournament.model_dump())
    db.add(new_tournament)
    await db.commit()
    await db.refresh(new_tournament)
    return new_tournament
