import asyncio
from src.database import SessionLocal
from src.coaches.crud import get_all_coaches
from src.athletes.crud import get_all_athletes

async def main():
    async with SessionLocal() as db:
        data = await get_all_coaches(db)
        for coach in data:
            print(f"ID: {coach.id}, Имя: {coach.first_name}, Фамилия: {coach.last_name}")

asyncio.run(main())
