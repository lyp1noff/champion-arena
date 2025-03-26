from fastapi import APIRouter, Request, HTTPException, Response
from jose import jwt
from datetime import datetime, timedelta, timezone
from src.config import JWT_SECRET, DEV_MODE

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login")
async def login(request: Request):
    data = await request.json()
    username = data.get("username")
    password = data.get("password")

    if (
        username != "qwe" or password != "qwe"
    ):  # TODO: Replace with actual authentication
        raise HTTPException(status_code=401, detail="Invalid credentials")

    expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    token = jwt.encode(
        {"sub": username, "role": "admin", "exp": expire},
        JWT_SECRET,
        algorithm="HS256",
    )

    response = Response(content="Login successful")
    response.set_cookie(
        key="token",
        value=token,
        httponly=True,
        secure=not DEV_MODE,
        samesite="lax",
        max_age=1800,
        path="/",
    )

    return {
        "access_token": token,
        "token_type": "bearer",
    }  # TODO: Make sepparate response model


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("token")
    return {"message": "Logged out"}
