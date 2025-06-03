from fastapi import Request, HTTPException
from jose import jwt, JWTError
from datetime import datetime, timezone
from src.config import JWT_SECRET


def get_current_user(request: Request):
    token = request.cookies.get("token")

    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[len("Bearer ") :]

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(
            timezone.utc
        ):
            raise HTTPException(status_code=401, detail="Token expired")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
