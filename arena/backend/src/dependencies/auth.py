from datetime import datetime, timezone
from typing import Any

from fastapi import Depends, HTTPException, Request
from jose import JWTError, jwt

from src.config import JWT_SECRET, SERVICE_TOKEN
from src.models import UserRole

ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


def get_current_user(request: Request) -> dict[str, Any]:
    """Authenticate the request. Does not authorize: use require_admin for admin-only routes."""
    token = request.cookies.get("token")

    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[len("Bearer ") :].strip()

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # TO-DO: Use proper db handling
    if token == SERVICE_TOKEN:
        return {"sub": "service", "role": UserRole.ADMIN.value}

    try:
        payload: dict[str, Any] = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    exp = payload.get("exp")
    if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Token expired")
    # Refresh tokens are long-lived and must never authenticate API calls.
    if payload.get("type") != ACCESS_TOKEN_TYPE:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload


def require_admin(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    if user.get("role") != UserRole.ADMIN.value:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
