import os
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Response
from starlette.responses import JSONResponse
from starlette.staticfiles import StaticFiles

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


app = FastAPI(lifespan=lifespan)
add_cors_middleware(app)


@app.middleware("http")
async def protect_docs(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    root = request.scope.get("root_path", "")
    path = request.url.path

    protected_prefixes = [
        f"{root}/docs",
        f"{root}/redoc",
        f"{root}/openapi.json",
    ]

    if any(path.startswith(p) for p in protected_prefixes):
        try:
            get_current_user(request)
        except HTTPException:
            return JSONResponse({"detail": "Not authenticated"}, status_code=401)

    return await call_next(request)


BASE_DIR = os.getcwd()
pdf_storage_path = os.path.join(BASE_DIR, "pdf_storage")
os.makedirs(pdf_storage_path, exist_ok=True)

app.mount("/pdf_storage", StaticFiles(directory=pdf_storage_path), name="static")
for router in routers:
    app.include_router(router)


@app.get("/ping", tags=["Health"])
async def ping() -> dict[str, bool]:
    return {"pong": True}
