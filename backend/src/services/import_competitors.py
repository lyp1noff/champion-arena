import json
import random
from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import (
    Tournament,
    Coach,
    Category,
    Athlete,
    # TournamentParticipant,
    Bracket,
    BracketParticipant,
)
from src.services.brackets import regenerate_tournament_brackets


# def random_date(start_year=2005, end_year=2017):
#     start_date = datetime(start_year, 1, 1)
#     end_date = datetime(end_year, 12, 31)
#     random_days = random.randint(0, (end_date - start_date).days)
#     return (start_date + timedelta(days=random_days)).date()


async def import_competitors_from_cbr(
    db: AsyncSession, tournament_id: int, content: bytes
):
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")

    result = await db.execute(select(Tournament).filter_by(id=tournament_id))
    tournament = result.scalars().first()

    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    coaches_cache = {}
    categories_cache = {}

    for competitor in data["Competitors"]:
        category_name = competitor["Category"]
        coach_name = competitor["Coach"]
        first_name = competitor.get("Name", "") or ""
        last_name = competitor["Surname"]

        # Coach
        if coach_name not in coaches_cache:
            result = await db.execute(select(Coach).filter_by(last_name=coach_name))
            coach = result.scalars().first()
            if not coach:
                coach = Coach(last_name=coach_name, first_name="")
                db.add(coach)
                await db.commit()
            coaches_cache[coach_name] = coach

        coach = coaches_cache[coach_name]

        # Category
        if category_name not in categories_cache:
            result = await db.execute(select(Category).filter_by(name=category_name))
            category = result.scalars().first()
            if not category:
                category = Category(name=category_name, age=0, gender="Unknown")
                db.add(category)
                await db.commit()
            categories_cache[category_name] = category

        category = categories_cache[category_name]

        # Athlete
        result = await db.execute(
            select(Athlete).filter_by(first_name=first_name, last_name=last_name)
        )
        athlete = result.scalars().first()
        if not athlete:
            # birth_date = random_date()
            athlete = Athlete(
                first_name=first_name,
                last_name=last_name,
                gender="male-or-female",
                # birth_date=birth_date,
                coach_id=coach.id,
            )
            db.add(athlete)
            await db.commit()

        # TournamentParticipant
        # result = await db.execute(
        #     select(TournamentParticipant).filter_by(
        #         tournament_id=tournament.id, athlete_id=athlete.id
        #     )
        # )
        # existing_participant = result.scalars().first()
        # if not existing_participant:
        #     tp = TournamentParticipant(
        #         tournament_id=tournament.id, athlete_id=athlete.id
        #     )
        #     db.add(tp)
        #     await db.commit()

        # Bracket
        result = await db.execute(
            select(Bracket).filter_by(
                tournament_id=tournament.id, category_id=category.id
            )
        )
        bracket = result.scalars().first()
        if not bracket:
            bracket = Bracket(tournament_id=tournament.id, category_id=category.id)
            db.add(bracket)
            await db.commit()

        # BracketParticipant
        participant = BracketParticipant(
            bracket_id=bracket.id,
            athlete_id=athlete.id,
            seed=competitor["SortId"],
        )
        db.add(participant)

    await db.commit()
    await regenerate_tournament_brackets(db, tournament.id)

    return {"status": "success", "message": "Data imported and brackets generated"}
