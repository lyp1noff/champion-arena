import asyncio

from src.database import SessionLocal
from src.services.auth import create_default_user


async def init() -> None:
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as db:
        await create_default_user(db)


if __name__ == "__main__":
    asyncio.run(init())
