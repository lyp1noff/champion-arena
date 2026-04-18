from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import DEV_MODE, JWT_SECRET
from src.database import get_db
from src.schemas import LoginRequest, TokenResponse
from src.services.auth import authenticate_user, create_refresh_token, create_token

ACCESS_TOKEN_EXPIRE_SECONDS = 60 * 30  # 30 minutes
REFRESH_TOKEN_EXPIRE_SECONDS = 60 * 60 * 24 * 7  # 7 days

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/token", response_model=TokenResponse)
async def get_bearer_token(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    user = await authenticate_user(db, data.username, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token(user.username, user.role, ACCESS_TOKEN_EXPIRE_SECONDS)
    return TokenResponse(access_token=token)


@router.post("/login")
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> Response:
    user = await authenticate_user(db, data.username, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_token(user.username, user.role, ACCESS_TOKEN_EXPIRE_SECONDS)
    refresh_token = create_refresh_token(user.username, REFRESH_TOKEN_EXPIRE_SECONDS)
    response = JSONResponse(
        content={
            "message": "Login successful",
            # "access_token": access_token,
            # "refresh_token": refresh_token,
        }
    )
    response.set_cookie(
        key="token",
        value=access_token,
        httponly=True,
        secure=not DEV_MODE,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_SECONDS,
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=not DEV_MODE,
        samesite="lax",
        max_age=REFRESH_TOKEN_EXPIRE_SECONDS,
        path="/",
    )
    return response


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: Request) -> Response:
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
            username, "admin", ACCESS_TOKEN_EXPIRE_SECONDS
        )  # Replace with actual role lookup if needed

        response = JSONResponse(
            # content={"access_token": access_token, "refresh_token": refresh_token}
            content={"message": "Token refreshed"}
        )
        response.set_cookie(
            key="token",
            value=access_token,
            httponly=True,
            secure=not DEV_MODE,
            samesite="lax",
            max_age=ACCESS_TOKEN_EXPIRE_SECONDS,
            path="/",
        )
        return response
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")


@router.post("/logout")
def logout(response: Response) -> dict[str, str]:
    response.delete_cookie("token", path="/")
    response.delete_cookie("refresh_token", path="/")
    return {"message": "Logged out"}
