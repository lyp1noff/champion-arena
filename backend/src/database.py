from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from src.config import SQLALCHEMY_DATABASE_URL

engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


async def get_db():
    async with SessionLocal() as session:
        yield session
