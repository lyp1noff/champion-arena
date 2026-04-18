import asyncio

import typer

from src.database import get_async_session
from src.models import Bracket, BracketState, BracketStatus, BracketType
from src.services import auth
from src.services.brackets import (
    regenerate_bracket_matches,
    regenerate_round_bracket_matches,
    regenerate_tournament_brackets,
)

cli = typer.Typer(help="CLI for admin operations")


@cli.command("set-password", help="Set a new password for an existing user")
def set_password(
    username: str = typer.Argument(..., help="Username of the account"),
    password: str = typer.Argument(..., help="New password to set"),
) -> None:
    ok: bool = asyncio.run(auth.set_password(username, password))
    if ok:
        typer.echo(f"Password updated for '{username}'")
    else:
        typer.echo(f"User '{username}' not found", err=True)
        raise typer.Exit(code=1)


@cli.command("create-admin", help="Create a new administrator account")
def create_admin(
    username: str = typer.Argument(..., help="Username for the new admin account"),
    password: str = typer.Argument(..., help="Password for the new admin account"),
) -> None:
    created: bool = asyncio.run(auth.create_admin(username, password))
    if created:
        typer.echo(f"Admin '{username}' created")
    else:
        typer.echo(f"User '{username}' already exists")


@cli.command("regenerate-tournament", help="Regenerate all brackets of a tournament by its ID")
def regenerate_tournament(
    tournament_id: int = typer.Argument(..., help="ID of the tournament to regenerate"),
) -> None:
    async def _run() -> None:
        async with get_async_session() as db:
            await regenerate_tournament_brackets(db, tournament_id)

    try:
        asyncio.run(_run())
        typer.echo(f"Tournament {tournament_id} regenerated")
    except Exception as e:
        typer.echo(f"Failed to regenerate tournament {tournament_id}: {e}", err=True)
        raise typer.Exit(code=1)


@cli.command("reset-bracket-draft", help="Set bracket to draft-like state and regenerate it by bracket ID")
def reset_bracket_draft(
    bracket_id: int = typer.Argument(..., help="ID of the bracket to reset"),
) -> None:
    async def _run() -> None:
        async with get_async_session() as db:
            bracket = await db.get(Bracket, bracket_id)
            if bracket is None:
                raise RuntimeError(f"Bracket {bracket_id} not found")

            bracket.state = BracketState.DRAFT.value
            bracket.status = BracketStatus.PENDING.value
            bracket.version += 1
            await db.commit()

            if bracket.type == BracketType.ROUND_ROBIN.value:
                await regenerate_round_bracket_matches(db, bracket.id, bracket.tournament_id)
            else:
                await regenerate_bracket_matches(db, bracket.id, bracket.tournament_id)

    try:
        asyncio.run(_run())
        typer.echo(f"Bracket {bracket_id} switched to draft and regenerated")
    except Exception as e:
        typer.echo(f"Failed to reset bracket {bracket_id}: {e}", err=True)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    cli()
