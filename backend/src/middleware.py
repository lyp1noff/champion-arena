from fastapi.middleware.cors import CORSMiddleware
from src.config import FRONTEND_URL

origins = [
    FRONTEND_URL,
]


def add_cors_middleware(app):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
