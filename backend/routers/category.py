from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from schemas import CategoryResponse
from database import get_db
from crud import get_categories

router = APIRouter()

@router.get("/categories", response_model=list[CategoryResponse])
async def get_all_categories(db: AsyncSession = Depends(get_db)):
    return await get_categories(db=db)
