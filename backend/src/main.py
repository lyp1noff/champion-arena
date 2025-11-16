import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from starlette.responses import JSONResponse
from starlette.staticfiles import StaticFiles

from src.config import DEV_MODE
from src.dependencies.auth import get_current_user
from src.middleware import add_cors_middleware
from src.routers import routers
from src.services.broadcast import broadcast


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    await broadcast.connect()
    try:
        yield
    finally:
        await broadcast.disconnect()


app = FastAPI(
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

if not DEV_MODE:
    @app.get("/docs", include_in_schema=False)
    async def custom_docs(user=Depends(get_current_user)):
        return get_swagger_ui_html(
            openapi_url="/openapi.json",
            title="API Docs"
        )

    @app.get("/redoc", include_in_schema=False)
    async def custom_redoc(user=Depends(get_current_user)):
        return get_redoc_html(
            openapi_url="/openapi.json",
            title="API ReDoc"
        )

    @app.get("/openapi.json", include_in_schema=False)
    async def custom_openapi(user=Depends(get_current_user)):
        return JSONResponse(app.openapi())

@app.get("/ping", tags=["Health"])
async def ping() -> dict[str, bool]:
    return {"pong": True}
