from fastapi import APIRouter, HTTPException, Response, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from src.schemas import LoginRequest, TokenResponse
from src.services.auth import authenticate_user, create_token
from src.database import get_db
from src.config import DEV_MODE

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
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    user = await authenticate_user(db, data.username, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token(user.username, user.role)
    response = JSONResponse(content={"message": "Login successful"})
    response.set_cookie(
        key="token",
        value=token,
        httponly=True,
        secure=not DEV_MODE,
        samesite="lax",
        max_age=3600 * 4,
        path="/",
    )
    return response


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("token")
    return {"message": "Logged out"}
