import asyncio

import typer

from src.database import get_async_session
from src.services import auth
from src.services.brackets import regenerate_tournament_brackets

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


if __name__ == "__main__":
    cli()
