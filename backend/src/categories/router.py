from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies.auth import get_current_user
from src.models import Category
from src.schemas import CategoryResponse
from src.database import get_db

router = APIRouter(
    prefix="/categories", tags=["Categories"], dependencies=[Depends(get_current_user)]
)


@router.get("", response_model=list[CategoryResponse])
async def get_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category))
    return result.scalars().all()
