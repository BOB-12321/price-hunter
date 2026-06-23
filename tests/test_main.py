"""Phase 1 smoke tests.

Verifies the FastAPI app boots, exposes the healthcheck, and serves the
mobile landing page.  These are real HTTP tests using httpx + ASGI
transport, so they don't need the database to be running.
"""
from __future__ import annotations

from typing import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    """ASGI client that doesn't talk to a real server."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_healthz_returns_ok(client: AsyncClient) -> None:
    res = await client.get("/healthz")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "env" in data


@pytest.mark.asyncio
async def test_index_serves_html(client: AsyncClient) -> None:
    res = await client.get("/")
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/html")
    body = res.text
    assert "Price Hunter" in body
    assert "/static/styles.css" in body
    assert "/static/app.js" in body


@pytest.mark.asyncio
async def test_static_css_served(client: AsyncClient) -> None:
    res = await client.get("/static/styles.css")
    assert res.status_code == 200
    assert ":root" in res.text  # sanity check the CSS file landed


@pytest.mark.asyncio
async def test_api_root_returns_endpoints(client: AsyncClient) -> None:
    res = await client.get("/api")
    assert res.status_code == 200
    data = res.json()
    assert data["service"] == "price-hunter"
    assert "/healthz" in data["endpoints"]["healthz"]
