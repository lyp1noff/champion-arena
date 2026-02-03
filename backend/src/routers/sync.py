from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.dependencies.auth import get_current_user
from src.schemas import SyncCommandsRequest, SyncCommandsResponse, SyncStatusResponse
from src.services.sync import apply_commands as apply_commands_service
from src.services.sync import get_status as get_status_service

router = APIRouter(prefix="/sync", tags=["Sync"], dependencies=[Depends(get_current_user)])


@router.post("/commands", response_model=SyncCommandsResponse)
async def sync_commands(
    payload: SyncCommandsRequest,
    db: AsyncSession = Depends(get_db),
) -> SyncCommandsResponse:
    return await apply_commands_service(db, payload)


@router.get("/status/{edge_id}", response_model=SyncStatusResponse)
async def sync_status(
    edge_id: str,
    db: AsyncSession = Depends(get_db),
) -> SyncStatusResponse:
    return await get_status_service(db, edge_id)
