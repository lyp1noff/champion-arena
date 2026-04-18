from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.dependencies.auth import get_current_user
from src.models import Category
from src.schemas import CategoryCreate, CategoryResponse

router = APIRouter(prefix="/categories", tags=["Categories"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[CategoryResponse])
async def get_categories(db: AsyncSession = Depends(get_db)) -> list[CategoryResponse]:
    result = await db.execute(select(Category))
    return [CategoryResponse.model_validate(c) for c in result.scalars().all()]


@router.post("", response_model=CategoryResponse)
async def create_category(category_data: CategoryCreate, db: AsyncSession = Depends(get_db)) -> CategoryResponse:
    new_category = Category(**category_data.model_dump())
    db.add(new_category)
    await db.commit()
    await db.refresh(new_category)
    return CategoryResponse.model_validate(new_category)
