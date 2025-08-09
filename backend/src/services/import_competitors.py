import json

from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import (
    Athlete,
    AthleteCoachLink,
    Bracket,
    BracketMatch,
    BracketParticipant,
    Category,
    Coach,
    Tournament,
)
from src.services.brackets import regenerate_tournament_brackets


async def import_competitors_from_cbr(db: AsyncSession, tournament_id: int, content: bytes) -> dict[str, str]:
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")

    result = await db.execute(select(Tournament).filter_by(id=tournament_id))
    tournament = result.scalars().first()

    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    brackets_result = await db.execute(select(Bracket).where(Bracket.tournament_id == tournament_id))
    brackets = brackets_result.scalars().all()
    for br in brackets:
        await db.execute(delete(BracketParticipant).where(BracketParticipant.bracket_id == br.id))
        await db.execute(delete(BracketMatch).where(BracketMatch.bracket_id == br.id))
    await db.commit()

    coaches_cache = {}
    categories_cache = {}

    for competitor in data["Competitors"]:
        category_name = competitor["Category"]
        coach_name = competitor["Coach"]
        first_name = competitor.get("Name", "") or ""
        last_name = competitor["Surname"]

        # Coach
        if coach_name not in coaches_cache:
            coach_result = await db.execute(select(Coach).filter_by(last_name=coach_name))
            coach = coach_result.scalars().first()
            if not coach:
                coach = Coach(last_name=coach_name, first_name="")
                db.add(coach)
                await db.commit()
            coaches_cache[coach_name] = coach

        coach = coaches_cache[coach_name]

        # Category
        if category_name not in categories_cache:
            category_result = await db.execute(select(Category).filter_by(name=category_name))
            category = category_result.scalars().first()
            if not category:
                category = Category(name=category_name, min_age=1, max_age=99, gender="male-or-female")
                db.add(category)
                await db.commit()
            categories_cache[category_name] = category

        category = categories_cache[category_name]

        # Athlete
        athlete_result = await db.execute(select(Athlete).filter_by(first_name=first_name, last_name=last_name))
        athlete = athlete_result.scalars().first()
        if not athlete:
            athlete = Athlete(
                first_name=first_name,
                last_name=last_name,
                gender="male-or-female",
            )
            db.add(athlete)
            await db.commit()

            # Create coach link
            coach_link = AthleteCoachLink(athlete_id=athlete.id, coach_id=coach.id)
            db.add(coach_link)
            await db.commit()

        # Bracket
        bracket_result = await db.execute(
            select(Bracket).filter_by(tournament_id=tournament.id, category_id=category.id)
        )
        bracket = bracket_result.scalar_one_or_none()
        if not bracket:
            bracket = Bracket(
                tournament_id=tournament.id,
                category_id=category.id,
            )
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
