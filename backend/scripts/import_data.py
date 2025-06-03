import os
import json
import asyncio
from datetime import date, datetime, timedelta
import random
from sqlalchemy import select

from src.database import SessionLocal
from src.models import (
    Bracket,
    BracketParticipant,
    Coach,
    Athlete,
    Category,
    Tournament,
    # TournamentParticipant,
)
from src.services.brackets import regenerate_tournament_brackets

DATA_FILE = os.path.join(os.path.dirname(__file__), "../data.cbr")

tournament_date = date(2023, 4, 12)


def random_date(start_year=2005, end_year=2017):
    start_date = datetime(start_year, 1, 1)
    end_date = datetime(end_year, 12, 31)
    random_days = random.randint(0, (end_date - start_date).days)
    return (start_date + timedelta(days=random_days)).date()


async def import_data():
    async with SessionLocal() as session:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        coaches_cache = {}
        categories_cache = {}

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

            # result = await session.execute(
            #     select(TournamentParticipant).filter_by(
            #         tournament_id=tournament.id, athlete_id=athlete.id
            #     )
            # )
            # existing_participant = result.scalars().first()
            # if not existing_participant:
            #     tournament_participant = TournamentParticipant(
            #         tournament_id=tournament.id, athlete_id=athlete.id
            #     )
            #     session.add(tournament_participant)
            #     await session.commit()

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

            participant = BracketParticipant(
                bracket_id=bracket.id, athlete_id=athlete.id, seed=competitor["SortId"]
            )
            session.add(participant)

        await session.commit()

        await regenerate_tournament_brackets(session, tournament.id)

    print("✅ Done!")


if __name__ == "__main__":
    asyncio.run(import_data())
