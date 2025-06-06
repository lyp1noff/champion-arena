import os
from fastapi import FastAPI
from contextlib import asynccontextmanager

from starlette.staticfiles import StaticFiles

from src.config import DEV_MODE
from src.middleware import add_cors_middleware
from src.database import SessionLocal, engine, Base
from src.routers import routers
from src.services.auth import create_default_user


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as session:
        await create_default_user(session)

    yield


app = FastAPI(
    root_path="/api",
    docs_url="/docs" if DEV_MODE else None,
    redoc_url="/redoc" if DEV_MODE else None,
    openapi_url="/openapi.json" if DEV_MODE else None,
    lifespan=lifespan,
)

add_cors_middleware(app)

BASE_DIR = os.getcwd()
pdf_storage_path = os.path.join(BASE_DIR, "pdf_storage")
os.makedirs(pdf_storage_path, exist_ok=True)

app.mount("/pdf_storage", StaticFiles(directory=pdf_storage_path), name="static")
for router in routers:
    app.include_router(router)
