from jose import jwt
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.models import User
from src.config import JWT_SECRET
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_token(username: str, role: str, expires_in: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    return jwt.encode(
        {"sub": username, "role": role, "exp": expire},
        JWT_SECRET,
        algorithm="HS256",
    )


def create_refresh_token(username: str, expires_in: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    return jwt.encode(
        {"sub": username, "exp": expire},
        JWT_SECRET,
        algorithm="HS256",
    )


async def authenticate_user(
    db: AsyncSession, username: str, password: str
) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


async def create_default_user(db: AsyncSession):
    result = await db.execute(select(User).where(User.username == "qwe"))  # CHANGE THIS
    user = result.scalar_one_or_none()

    if user is None:
        # raw_password = secrets.token_urlsafe(9)
        # hashed = hash_password(raw_password)

        # user = User(username="admin", password_hash=hashed, role="admin")

        user = User(username="qwe", password_hash=hash_password("qwe"), role="admin")
        db.add(user)
        await db.commit()

        print(f"[+] Default admin created")
        # print(f"    Username: admin")
        # print(f"    Password: {raw_password}")
    # else:
    #     print("[✓] Default admin already exists")
