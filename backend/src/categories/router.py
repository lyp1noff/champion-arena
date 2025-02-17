from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas import CategoryResponse
from src.database import get_db
from src.categories.crud import get_all_categories as crud_get_all_categories

router = APIRouter()

@router.get("/categories", response_model=list[CategoryResponse])
async def get_categories(db: AsyncSession = Depends(get_db)):
    return await crud_get_all_categories(db=db)
