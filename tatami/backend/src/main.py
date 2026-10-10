from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import DEV_MODE
from src.routers import routers


app = FastAPI(
    root_path="/api",
    docs_url="/docs" if DEV_MODE else None,
    redoc_url="/redoc" if DEV_MODE else None,
    openapi_url="/openapi.json" if DEV_MODE else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in routers:
    app.include_router(router)
