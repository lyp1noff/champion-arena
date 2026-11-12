from datetime import date

import pytest
import pytest_asyncio
from httpx import AsyncClient
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from src import config
from src.config import JWT_SECRET, SERVICE_TOKEN
from src.models import Tournament, User
from src.services.auth import create_refresh_token, create_token, hash_password


@pytest_asyncio.fixture
async def tournament_id(db_session: AsyncSession) -> int:
    tournament = Tournament(
        name="T",
        location="L",
        start_date=date(2026, 1, 10),
        end_date=date(2026, 1, 11),
        registration_start_date=date(2026, 1, 1),
        registration_end_date=date(2026, 1, 5),
    )
    db_session.add(tournament)
    await db_session.commit()
    return tournament.id


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _add_user(db: AsyncSession, username: str, role: str) -> None:
    db.add(User(username=username, password_hash=hash_password("pw"), role=role))
    await db.commit()


@pytest.mark.asyncio
async def test_applications_require_authentication(anon_client: AsyncClient, tournament_id: int) -> None:
    payload = {"tournament_id": tournament_id, "athlete_id": 1, "category_id": 1}

    assert (await anon_client.get(f"/tournaments/{tournament_id}/applications")).status_code == 401
    assert (await anon_client.post(f"/tournaments/{tournament_id}/applications", json=payload)).status_code == 401


@pytest.mark.asyncio
async def test_non_admin_token_is_forbidden_on_admin_routes(anon_client: AsyncClient, tournament_id: int) -> None:
    token = create_token("coach", "user", 60)

    responses = [
        await anon_client.get(f"/tournaments/{tournament_id}/applications", headers=bearer(token)),
        await anon_client.post(f"/tournaments/{tournament_id}/applications/approve-all", headers=bearer(token)),
        await anon_client.delete(f"/tournaments/{tournament_id}", headers=bearer(token)),
        await anon_client.get("/athletes", headers=bearer(token)),
        await anon_client.post("/sync/upserts", headers=bearer(token), json={}),
    ]

    assert [response.status_code for response in responses] == [403] * len(responses)


@pytest.mark.asyncio
async def test_admin_and_service_tokens_are_allowed(anon_client: AsyncClient, tournament_id: int) -> None:
    admin_token = create_token("admin", "admin", 60)

    admin_response = await anon_client.get(f"/tournaments/{tournament_id}/applications", headers=bearer(admin_token))
    service_response = await anon_client.get(
        f"/tournaments/{tournament_id}/applications", headers=bearer(SERVICE_TOKEN)
    )

    assert admin_response.status_code == 200
    assert service_response.status_code == 200


@pytest.mark.asyncio
async def test_public_reads_stay_public(anon_client: AsyncClient, tournament_id: int) -> None:
    assert (await anon_client.get("/tournaments")).status_code == 200
    assert (await anon_client.get(f"/tournaments/{tournament_id}")).status_code == 200


@pytest.mark.asyncio
async def test_refresh_token_cannot_authenticate_api_calls(anon_client: AsyncClient, tournament_id: int) -> None:
    refresh = create_refresh_token("admin", 60)

    response = await anon_client.get(f"/tournaments/{tournament_id}/applications", headers=bearer(refresh))

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_issues_role_from_database(anon_client: AsyncClient, db_session: AsyncSession) -> None:
    await _add_user(db_session, "coach", "user")

    response = await anon_client.post(
        "/auth/refresh", headers={"Cookie": f"refresh_token={create_refresh_token('coach', 60)}"}
    )

    assert response.status_code == 200
    access_token = response.cookies.get("token")
    assert access_token is not None
    claims = jwt.decode(access_token, JWT_SECRET, algorithms=["HS256"])
    assert claims["role"] == "user"
    assert claims["type"] == "access"


@pytest.mark.asyncio
async def test_refresh_rejects_unknown_user_and_access_tokens(
    anon_client: AsyncClient, db_session: AsyncSession
) -> None:
    await _add_user(db_session, "admin", "admin")

    unknown = await anon_client.post(
        "/auth/refresh", headers={"Cookie": f"refresh_token={create_refresh_token('ghost', 60)}"}
    )
    access_as_refresh = await anon_client.post(
        "/auth/refresh", headers={"Cookie": f"refresh_token={create_token('admin', 'admin', 60)}"}
    )

    assert unknown.status_code == 401
    assert access_as_refresh.status_code == 401


def test_runtime_secrets_rejected_outside_dev_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "DEV_MODE", False)
    monkeypatch.setattr(config, "JWT_SECRET", "secret")
    monkeypatch.setattr(config, "SERVICE_TOKEN", "a-long-random-service-token-value")

    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        config.validate_runtime_secrets()

    monkeypatch.setattr(config, "JWT_SECRET", "a-long-random-jwt-secret-value")
    config.validate_runtime_secrets()

    monkeypatch.setattr(config, "DEV_MODE", True)
    monkeypatch.setattr(config, "JWT_SECRET", "secret")
    config.validate_runtime_secrets()
