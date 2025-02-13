from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from contextlib import asynccontextmanager

from models import *
from schemas import *
from database import get_db, engine, Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/coaches", response_model=list[CoachResponse])
async def get_coaches(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Coach))
    return result.scalars().all()

@app.get("/coach/{id}", response_model=CoachResponse)
async def get_coach(id: int, db: AsyncSession = Depends(get_db)):    
    result = await db.execute(select(Coach).filter(Coach.id == id))
    coach = result.scalars().first()
    if coach is None:
        raise HTTPException(status_code=404, detail="Coach not found")
    return coach

@app.post("/coach", response_model=CoachResponse)
async def create_coach(coach: CoachCreate, db: AsyncSession = Depends(get_db)):
    new_coach = Coach(**coach.model_dump())
    db.add(new_coach)
    await db.commit()
    await db.refresh(new_coach)
    return new_coach

@app.get("/athletes", response_model=list[AthleteResponse])
async def get_athletes(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Athlete))
    return result.scalars().all()

@app.get("/athlete/{id}", response_model=AthleteResponse)
async def get_athlete(id: int, db: AsyncSession = Depends(get_db)):    
    result = await db.execute(select(Athlete).filter(Athlete.id == id))
    athlete = result.scalars().first()
    if athlete is None:
        raise HTTPException(status_code=404, detail="Athlete not found")
    return athlete

@app.post("/athlete", response_model=AthleteResponse)
async def create_athlete(athlete: AthleteCreate, db: AsyncSession = Depends(get_db)):
    new_athlete = Athlete(**athlete.model_dump())
    db.add(new_athlete)
    await db.commit()
    await db.refresh(new_athlete)
    return new_athlete

@app.get("/tournaments", response_model=list[TournamentResponse])
async def get_tournaments(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tournament))
    return result.scalars().all()

@app.get("/tournament/{id}", response_model=TournamentResponse)
async def get_tournament(id: int, db: AsyncSession = Depends(get_db)):    
    result = await db.execute(select(Tournament).filter(Tournament.id == id))
    tournament = result.scalars().first()
    if tournament is None:
        raise HTTPException(status_code=404, detail="Tournament not found")
    return tournament

@app.post("/tournament", response_model=TournamentResponse)
async def create_tournament(tournament: TournamentCreate, db: AsyncSession = Depends(get_db)):
    new_tournament = Tournament(**tournament.model_dump())
    db.add(new_tournament)
    await db.commit()
    await db.refresh(new_tournament)
    return new_tournament

@app.get("/categories", response_model=list[CategoryResponse])
async def get_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category))
    return result.scalars().all()