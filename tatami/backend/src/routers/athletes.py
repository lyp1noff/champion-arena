from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models import Athlete
from src.schemas import AthleteSchema

router = APIRouter(
    prefix="/athletes",
    tags=["Athletes"],
)


@router.get("", response_model=list[AthleteSchema])
async def get_local_athletes(db: AsyncSession = Depends(get_db)) -> list[AthleteSchema]:
    result = await db.execute(select(Athlete).order_by(Athlete.last_name, Athlete.first_name, Athlete.id))
    return [AthleteSchema.model_validate(athlete) for athlete in result.scalars().all()]
