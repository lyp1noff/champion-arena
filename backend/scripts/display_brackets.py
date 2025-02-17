import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.database import get_db
from src.models import Bracket, BracketParticipant, Athlete, Category

async def display_brackets(tournament_id: int, filename: str = "brackets_output.txt"):
    """Выводит турнирные сетки для указанного турнира и сохраняет в файл."""

    output_lines = []  # Список для строк вывода

    async for session in get_db():  # Используем get_db()
        # Получаем все сетки для турнира
        result = await session.execute(
            select(Bracket).filter_by(tournament_id=tournament_id).order_by(Bracket.id)
        )
        brackets = result.scalars().all()

        if not brackets:
            output_lines.append(f"❌ В турнире {tournament_id} нет сеток.")
            break

        for bracket in brackets:
            # Получаем категорию
            category_result = await session.execute(
                select(Category).filter_by(id=bracket.category_id)
            )
            category = category_result.scalars().first()

            if not category:
                continue  # Пропускаем, если категория не найдена

            output_lines.append(f"\n{category.name}")  # Заголовок категории

            # Получаем участников сетки, сортируем по `seed`
            participants_result = await session.execute(
                select(BracketParticipant)
                .filter_by(bracket_id=bracket.id)
                .order_by(BracketParticipant.seed)
            )
            participants = participants_result.scalars().all()

            for idx, participant in enumerate(participants, start=1):
                # Получаем атлета
                athlete_result = await session.execute(
                    select(Athlete).filter_by(id=participant.athlete_id)
                )
                athlete = athlete_result.scalars().first()

                if athlete:
                    output_lines.append(f"{idx}. {athlete.last_name} {athlete.first_name}")

    # Записываем результат в файл
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))

    print(f"✅ Результаты сохранены в файл: {filename}")

# Запуск скрипта вручную
if __name__ == "__main__":
    tournament_id = int(input("Введите ID турнира: "))  # Запрос ID
    asyncio.run(display_brackets(tournament_id))
