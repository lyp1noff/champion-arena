from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.middleware import add_cors_middleware

from src.database import engine, Base
from src.coaches import router as coach
from src.athletes import router as athlete
from src.tournaments import router as tournament
from src.categories import router as category

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(lifespan=lifespan)

add_cors_middleware(app)

app.include_router(coach.router)
app.include_router(athlete.router)
app.include_router(tournament.router)
app.include_router(category.router)


@app.get("/")
def get_root():
    return {"Hello": "World"}
