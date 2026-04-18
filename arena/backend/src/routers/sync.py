from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.dependencies.auth import get_current_user
from src.schemas import SyncStatusResponse, SyncUpsertsRequest, SyncUpsertsResponse
from src.services.sync import get_status as get_status_service
from src.services.sync import apply_upserts as apply_upserts_service

router = APIRouter(prefix="/sync", tags=["Sync"], dependencies=[Depends(get_current_user)])


@router.post("/upserts", response_model=SyncUpsertsResponse)
async def sync_upserts(
    payload: SyncUpsertsRequest,
    db: AsyncSession = Depends(get_db),
) -> SyncUpsertsResponse:
    return await apply_upserts_service(db, payload)


@router.get("/status/{edge_id}", response_model=SyncStatusResponse)
async def sync_status(
    edge_id: str,
    tournament_id: int,
    db: AsyncSession = Depends(get_db),
) -> SyncStatusResponse:
    return await get_status_service(db, edge_id, tournament_id)
