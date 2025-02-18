from fastapi.middleware.cors import CORSMiddleware
from src.config import FRONTEND_URL

def add_cors_middleware(app):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[FRONTEND_URL],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
