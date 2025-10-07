import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt
from passlib.context import CryptContext
from sqlalchemy import delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.config import DEV_MODE, JWT_SECRET
from src.database import get_async_session
from src.logger import logger
from src.models import User

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> Any:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> Any:
    return pwd_context.verify(plain, hashed)


def create_token(username: str, role: str, expires_in: int) -> Any:
    expire = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    return jwt.encode(
        {"sub": username, "role": role, "exp": expire},
        JWT_SECRET,
        algorithm="HS256",
    )


def create_refresh_token(username: str, expires_in: int) -> Any:
    expire = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    return jwt.encode(
        {"sub": username, "exp": expire},
        JWT_SECRET,
        algorithm="HS256",
    )


async def authenticate_user(db: AsyncSession, username: str, password: str) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


async def create_default_user(db: AsyncSession) -> None:
    if not DEV_MODE:
        await db.execute(delete(User).where(User.username.in_(["qwe", "test", "demo"])))
        await db.commit()

    result = await db.execute(select(func.count()).select_from(User))
    count = result.scalar_one()

    if count == 0:
        raw_password = secrets.token_urlsafe(12)
        hashed = hash_password(raw_password)

        user = User(username="champ", password_hash=hashed, role="admin")
        db.add(user)
        await db.commit()

        logger.info("Default admin created")
        logger.info("    Username: champ")
        logger.info(f"    Password: {raw_password}")


async def set_password(username: str, password: str) -> bool:
    async with get_async_session() as session:
        result = await session.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()

        if not user:
            return False

        user.password_hash = hash_password(password)
        await session.commit()
        return True


async def create_admin(username: str, password: str) -> bool:
    async with get_async_session() as session:
        result = await session.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()

        if user:
            return False

        new_user = User(
            username=username,
            password_hash=hash_password(password),
            role="admin",
        )
        session.add(new_user)
        await session.commit()
        return True
