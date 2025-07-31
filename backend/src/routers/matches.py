from fastapi import APIRouter, Body, Depends, HTTPException

# from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.dependencies.auth import get_current_user
from src.models import (  # BracketMatch,
    Match,
    MatchStatus,
)

router = APIRouter(prefix="/matches", tags=["Matches"], dependencies=[Depends(get_current_user)])


# @router.post("/{id}/finish")
# async def finish_match(
#     id: int,
#     result: MatchResultSchema,
#     db: AsyncSession = Depends(get_db),
# ):
#     match = await db.get(Match, id)
#     if not match:
#         raise HTTPException(404, "Match not found")
#     if match.is_finished:
#         raise HTTPException(400, "Match already finished")

#     match.score_athlete1 = result.score_athlete1
#     match.score_athlete2 = result.score_athlete2
#     match.winner_id = result.winner_id
#     match.is_finished = True

#     # Найти следующую ячейку, если есть
#     bm_result = await db.execute(
#         select(BracketMatch).where(BracketMatch.match_id == match.id)
#     )
#     bm = bm_result.scalar_one_or_none()
#     if bm and bm.next_slot is not None:
#         next_match = await db.execute(
#             select(BracketMatch).where(
#                 BracketMatch.bracket_id == bm.bracket_id,
#                 BracketMatch.round_number == bm.round_number + 1,
#                 BracketMatch.position == bm.next_slot,
#             )
#         )
#         next = next_match.scalar_one_or_none()
#         if next:
#             # Кто станет athlete1/2 зависит от чётности позиции
#             if bm.position % 2 == 1:
#                 next.match.athlete1_id = match.winner_id
#             else:
#                 next.match.athlete2_id = match.winner_id

#     await db.commit()
#     return {"status": "ok"}


@router.patch("/{id}/status")
async def update_match_status(
    id: int,
    status: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
):
    match = await db.get(Match, id)
    if not match:
        raise HTTPException(404, "Match not found")
    if status not in [s.value for s in MatchStatus]:
        raise HTTPException(400, f"Invalid status: {status}")
    match.status = status
    await db.commit()
    await db.refresh(match)
    return match
