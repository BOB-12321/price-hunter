"""Admin endpoint tests."""
from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.config import settings
from app.db import Base, engine


@pytest_asyncio.fixture(autouse=True)
async def _reset_schema():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=__import__("app.main", fromlist=["app"]).app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_seed_requires_token(client: AsyncClient) -> None:
    res = await client.post("/api/admin/seed")
    assert res.status_code in (401, 503)


@pytest.mark.asyncio
async def test_seed_with_valid_token(client: AsyncClient) -> None:
    settings.admin_token = "test-token-xyz"
    try:
        res = await client.post(
            "/api/admin/seed", headers={"X-Seed-Token": "test-token-xyz"}
        )
        assert res.status_code == 200, res.text
        body = res.json()
        assert body["status"] == "ok"
        assert body["stores_added"] > 0

        # Idempotent
        res = await client.post(
            "/api/admin/seed", headers={"X-Seed-Token": "test-token-xyz"}
        )
        assert res.status_code == 200
        assert res.json()["stores_added"] == 0
    finally:
        settings.admin_token = ""


@pytest.mark.asyncio
async def test_seed_rejects_bad_token(client: AsyncClient) -> None:
    settings.admin_token = "test-token-xyz"
    try:
        res = await client.post(
            "/api/admin/seed", headers={"X-Seed-Token": "wrong"}
        )
        assert res.status_code == 401
    finally:
        settings.admin_token = ""
