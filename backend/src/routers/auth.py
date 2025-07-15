from fastapi import APIRouter, HTTPException, Response, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from src.schemas import LoginRequest, TokenResponse
from src.services.auth import authenticate_user, create_token, create_refresh_token
from src.database import get_db
from src.config import DEV_MODE, JWT_SECRET
from jose import jwt, JWTError

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/token", response_model=TokenResponse)
async def get_bearer_token(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    user = await authenticate_user(db, data.username, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token(user.username, user.role)
    return TokenResponse(access_token=token)


@router.post("/login")
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    user = await authenticate_user(db, data.username, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_token(user.username, user.role)
    refresh_token = create_refresh_token(user.username)
    response = JSONResponse(
        content={
            "message": "Login successful",
            "access_token": access_token,
            "refresh_token": refresh_token,
        }
    )
    response.set_cookie(
        key="token",
        value=access_token,
        httponly=True,
        secure=not DEV_MODE,
        samesite="lax",
        max_age=3600 * 4,
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=not DEV_MODE,
        samesite="lax",
        max_age=3600 * 24 * 7,
        path="/",
    )
    return response


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: Request):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token provided")
    try:
        payload = jwt.decode(refresh_token, JWT_SECRET, algorithms=["HS256"])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        # Optionally: fetch user and role from DB
        access_token = create_token(
            username, "admin"
        )  # Replace with actual role lookup if needed
        return TokenResponse(access_token=access_token, refresh_token=refresh_token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("token")
    return {"message": "Logged out"}
