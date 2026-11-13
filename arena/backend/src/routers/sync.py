from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.dependencies.auth import require_admin
from src.schemas import SyncBracketsRequest, SyncBracketsResponse
from src.services.sync import apply_brackets

router = APIRouter(prefix="/sync", tags=["Sync"], dependencies=[Depends(require_admin)])


@router.put("/brackets", response_model=SyncBracketsResponse)
async def sync_brackets(payload: SyncBracketsRequest, db: AsyncSession = Depends(get_db)) -> SyncBracketsResponse:
    return await apply_brackets(db, payload)
