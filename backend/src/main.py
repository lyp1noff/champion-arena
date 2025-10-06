import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.staticfiles import StaticFiles

from src.services.broadcast import broadcast
from src.config import DEV_MODE
from src.middleware import add_cors_middleware
from src.routers import routers


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    await broadcast.connect()
    try:
        yield
    finally:
        await broadcast.disconnect()


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


@app.get("/ping", tags=["Health"])
async def ping():
    return {"pong": True}
