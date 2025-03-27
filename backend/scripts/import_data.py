import os
import json
import asyncio
from datetime import date, datetime, timedelta
import random
from sqlalchemy import select

# Импорт базы данных и моделей
from src.database import SessionLocal
from src.models import (
    BracketMatch,
    Tournament,
    Coach,
    Athlete,
    Category,
    Bracket,
    BracketParticipant,
    TournamentParticipant,
)

# Путь к JSON-файлу
DATA_FILE = os.path.join(os.path.dirname(__file__), "../data.cbr")

# Установленные даты
tournament_date = date(2023, 4, 12)


def random_date(start_year=2005, end_year=2017):
    start_date = datetime(start_year, 1, 1)
    end_date = datetime(end_year, 12, 31)
    random_days = random.randint(0, (end_date - start_date).days)
    return (start_date + timedelta(days=random_days)).date()


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
        tournament = Tournament(
            name="Example Tournament",
            location="Somewhere",
            start_date=tournament_date,
            end_date=tournament_date + timedelta(days=3),
            registration_start_date=tournament_date - timedelta(days=10),
            registration_end_date=tournament_date - timedelta(days=1),
        )
        session.add(tournament)
        await session.commit()

        for competitor in data["Competitors"]:
            category_name = competitor["Category"]
            coach_name = competitor["Coach"]
            first_name = competitor["Name"] if competitor["Name"] else ""
            last_name = competitor["Surname"]

            # Получаем или создаём тренера
            if coach_name not in coaches_cache:
                result = await session.execute(
                    select(Coach).filter_by(last_name=coach_name)
                )
                coach = result.scalars().first()
                if not coach:
                    coach = Coach(last_name=coach_name, first_name="")
                    session.add(coach)
                    await session.commit()
                coaches_cache[coach_name] = coach

            coach = coaches_cache[coach_name]

            # Получаем или создаём категорию
            if category_name not in categories_cache:
                result = await session.execute(
                    select(Category).filter_by(name=category_name)
                )
                category = result.scalars().first()
                if not category:
                    category = Category(name=category_name, age=0, gender="Unknown")
                    session.add(category)
                    await session.commit()
                categories_cache[category_name] = category

            category = categories_cache[category_name]

            # Создаём атлета
            result = await session.execute(
                select(Athlete).filter_by(first_name=first_name, last_name=last_name)
            )
            athlete = result.scalars().first()
            if not athlete:
                birth_date = random_date()
                athlete = Athlete(
                    first_name=first_name,
                    last_name=last_name,
                    gender="male-or-female",
                    birth_date=birth_date,
                    coach_id=coach.id,
                )
                session.add(athlete)
                await session.commit()

            result = await session.execute(
                select(TournamentParticipant).filter_by(
                    tournament_id=tournament.id, athlete_id=athlete.id
                )
            )
            existing_participant = result.scalars().first()

            if not existing_participant:
                tournament_participant = TournamentParticipant(
                    tournament_id=tournament.id, athlete_id=athlete.id
                )
                session.add(tournament_participant)
                await session.commit()

            # Создаём сетку, если её нет
            result = await session.execute(
                select(Bracket).filter_by(
                    tournament_id=tournament.id, category_id=category.id
                )
            )
            bracket = result.scalars().first()
            if not bracket:
                bracket = Bracket(tournament_id=tournament.id, category_id=category.id)
                session.add(bracket)
                await session.commit()

            # Добавляем участника в сетку
            participant = BracketParticipant(
                bracket_id=bracket.id, athlete_id=athlete.id, seed=competitor["SortId"]
            )
            session.add(participant)

        # Финальный коммит
        await session.commit()

        result = await session.execute(select(Bracket))
        brackets = result.scalars().all()

        for bracket in brackets:
            result = await session.execute(
                select(BracketParticipant)
                .filter_by(bracket_id=bracket.id)
                .order_by(BracketParticipant.seed)
            )
            participants = result.scalars().all()
            athletes = [p.athlete_id for p in participants if p.athlete_id is not None]

            # Добавим "TBD" если нечетное количество
            if len(athletes) % 2 != 0:
                athletes.append(None)

            for i in range(0, len(athletes), 2):
                match = BracketMatch(
                    bracket_id=bracket.id,
                    round_number=1,
                    position=(i // 2) + 1,
                    athlete1_id=athletes[i],
                    athlete2_id=athletes[i + 1] if i + 1 < len(athletes) else None,
                )
                session.add(match)

        await session.commit()

    print("✅ Импорт данных завершён!")


# Запускаем импорт
if __name__ == "__main__":
    asyncio.run(import_data())
