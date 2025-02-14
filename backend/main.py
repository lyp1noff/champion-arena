from fastapi import FastAPI
from contextlib import asynccontextmanager

from database import engine, Base
from middleware import add_cors_middleware
from routers import coach, athlete, tournament, category

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
def read_root():
    return {"Hello": "World"}
