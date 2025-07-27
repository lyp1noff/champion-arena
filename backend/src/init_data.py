import asyncio
from src.database import engine, Base, SessionLocal
from src.services.auth import create_default_user


async def init():
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as session:
        await create_default_user(session)


if __name__ == "__main__":
    asyncio.run(init())
