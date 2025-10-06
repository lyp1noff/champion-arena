from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from src.config import SQLALCHEMY_DATABASE_URL
from src.logger import logger

engine: AsyncEngine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=False)

SessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)

Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as db:
        try:
            yield db
        except Exception as e:
            logger.error(f"Session {id(db)} error: {e}")
            await db.rollback()
            raise
        finally:
            if db.in_transaction():
                await db.rollback()
            logger.debug(f"Session {id(db)} closed")


@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as db:
        yield db
