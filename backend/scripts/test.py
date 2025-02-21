import asyncio

from sqlalchemy import func, select
from src.database import SessionLocal
from src.models import Athlete


async def main():
    async with SessionLocal() as db:
        search_term = "%Іванунік%"
        query = (
            select(func.count())
            .select_from(Athlete)
            .where(Athlete.last_name.ilike(search_term))
        )

        result = await db.execute(query)
        total = result.scalar_one_or_none() or 0

        print(f"🔍 Найдено записей: {total}")


asyncio.run(main())
