import os

os.environ["APP_ENV"] = "test"

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from backend.config import clear_settings_cache
from backend.database import ensure_indexes
from backend.main import create_app


@pytest.fixture
async def client():
    clear_settings_cache()
    app = create_app()
    async with LifespanManager(app):
        await app.state.mongo_client.drop_database(app.state.mongo_db.name)
        await ensure_indexes(app.state.mongo_db)
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as test_client:
            test_client.app = app
            yield test_client
        await app.state.mongo_client.drop_database(app.state.mongo_db.name)


@pytest.fixture
async def registered_user(client: AsyncClient) -> dict:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "name": "Ada",
            "email": "ada@example.com",
            "password": "Password123!",
            "device_type": "cli",
        },
    )
    assert response.status_code == 201
    token = response.json()["access_token"]
    me_response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    return {"token": token, "user": me_response.json()}
