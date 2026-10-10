from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from src.config import SQLALCHEMY_DATABASE_URL

engine: AsyncEngine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=False)

SessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as db:
        yield db


async def prepare_database() -> None:
    from src.migrations import OUTBOX_MIGRATION_LOCK_ID, migrate_outbox_schema
    from src.models import Base

    async with engine.begin() as connection:
        await connection.execute(
            text("SELECT pg_advisory_xact_lock(:lock_id)"),
            {"lock_id": OUTBOX_MIGRATION_LOCK_ID},
        )
        await connection.run_sync(Base.metadata.create_all)
        await migrate_outbox_schema(connection)
