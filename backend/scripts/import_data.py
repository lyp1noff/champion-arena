import datetime
import os
import json
import asyncio
from sqlalchemy import select

# Импорт базы данных и моделей
from src.database import SessionLocal
from src.models import Tournament, Coach, Athlete, Category, Bracket, BracketParticipant

# Путь к JSON-файлу
DATA_FILE = os.path.join(os.path.dirname(__file__), "../data.cbr")

temp_date=datetime.date.today()

async def import_data():
    """Импорт данных из JSON в базу данных"""
    async with SessionLocal() as session:
        # Загружаем JSON
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Кэшируем тренеров и категории
        coaches_cache = {}
        categories_cache = {}

        # Создаём турнир (можно параметризовать)
        tournament = Tournament(name="Example Tournament", location="Somewhere", start_date=temp_date, end_date=temp_date, registration_start_date=temp_date, registration_end_date=temp_date)
        session.add(tournament)
        await session.commit()

        for competitor in data["Competitors"]:
            category_name = competitor["Category"]
            coach_name = competitor["Coach"]
            first_name = competitor["Name"] if competitor["Name"] else ""
            last_name = competitor["Surname"]

            # Получаем или создаём тренера
            if coach_name not in coaches_cache:
                result = await session.execute(select(Coach).filter_by(last_name=coach_name))
                coach = result.scalars().first()
                if not coach:
                    coach = Coach(last_name=coach_name, first_name="")
                    session.add(coach)
                    await session.commit()
                coaches_cache[coach_name] = coach

            coach = coaches_cache[coach_name]

            # Получаем или создаём категорию
            if category_name not in categories_cache:
                result = await session.execute(select(Category).filter_by(name=category_name))
                category = result.scalars().first()
                if not category:
                    category = Category(name=category_name, age=0, gender="Unknown")
                    session.add(category)
                    await session.commit()
                categories_cache[category_name] = category

            category = categories_cache[category_name]

            # Создаём атлета
            result = await session.execute(select(Athlete).filter_by(first_name=first_name, last_name=last_name))
            athlete = result.scalars().first()
            if not athlete:
                athlete = Athlete(
                    first_name=first_name,
                    last_name=last_name,
                    gender="Unknown",
                    birth_date=temp_date,
                    coach_id=coach.id
                )
                session.add(athlete)
                await session.commit()

            # Создаём сетку, если её нет
            result = await session.execute(select(Bracket).filter_by(tournament_id=tournament.id, category_id=category.id))
            bracket = result.scalars().first()
            if not bracket:
                bracket = Bracket(tournament_id=tournament.id, category_id=category.id)
                session.add(bracket)
                await session.commit()

            # Добавляем участника в сетку
            participant = BracketParticipant(bracket_id=bracket.id, athlete_id=athlete.id, seed=competitor["SortId"])
            session.add(participant)

        # Финальный коммит
        await session.commit()

    print("✅ Импорт данных завершён!")

# Запускаем импорт
if __name__ == "__main__":
    asyncio.run(import_data())
