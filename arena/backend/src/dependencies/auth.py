from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, Request
from jose import JWTError, jwt

from src.config import JWT_SECRET, SERVICE_TOKEN


def get_current_user(request: Request) -> dict[str, Any]:
    token = request.cookies.get("token")

    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[len("Bearer ") :].strip()

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # TO-DO: Use proper db handling
    if token == SERVICE_TOKEN:
        return {"sub": "service", "role": "admin"}

    try:
        payload: dict[str, Any] = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
            raise HTTPException(status_code=401, detail="Token expired")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
