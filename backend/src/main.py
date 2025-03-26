from fastapi import FastAPI
from contextlib import asynccontextmanager

from src.config import DEV_MODE
from src.middleware import add_cors_middleware
from src.database import engine, Base
from src.coaches import router as coach
from src.athletes import router as athlete
from src.tournaments import router as tournament
from src.categories import router as category
from src.brackets import router as bracket
from src.upload import router as upload
from src.auth import router as auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    root_path="/api",
    docs_url="/docs" if DEV_MODE else None,
    redoc_url="/redoc" if DEV_MODE else None,
    openapi_url="/openapi.json" if DEV_MODE else None,
    lifespan=lifespan,
)

add_cors_middleware(app)

app.include_router(coach.router)
app.include_router(athlete.router)
app.include_router(tournament.router)
app.include_router(category.router)
app.include_router(bracket.router)
app.include_router(upload.router)
app.include_router(auth.router)
