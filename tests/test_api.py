"""End-to-end tests for the Phase 2 CRUD API.

The conftest sets DATABASE_URL to an in-memory SQLite; the per-test
fixture drops + recreates tables for full isolation.
"""
from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app import models
from app.db import Base, engine
from app.main import app


@pytest_asyncio.fixture(autouse=True)
async def _reset_schema() -> AsyncIterator[None]:
    """Drop + recreate all tables around every test for full isolation."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ---- Healthcheck still works --------------------------------------------


@pytest.mark.asyncio
async def test_healthz_still_ok(client: AsyncClient) -> None:
    res = await client.get("/healthz")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


# ---- Products -----------------------------------------------------------


@pytest.mark.asyncio
async def test_product_crud_round_trip(client: AsyncClient) -> None:
    # Create
    res = await client.post("/api/products", json={
        "name": "Lurpak Butter 250g",
        "brand": "Lurpak",
        "size": "250g",
        "category": "Dairy",
    })
    assert res.status_code == 201, res.text
    created = res.json()
    assert created["id"] > 0
    assert created["name"] == "Lurpak Butter 250g"

    # List
    res = await client.get("/api/products")
    assert res.status_code == 200
    items = res.json()
    assert len(items) == 1
    assert items[0]["name"] == created["name"]

    # Get one
    res = await client.get(f"/api/products/{created['id']}")
    assert res.status_code == 200
    assert res.json()["id"] == created["id"]

    # Patch
    res = await client.patch(f"/api/products/{created['id']}",
                              json={"notes": "Closer price at Lidl"})
    assert res.status_code == 200
    assert res.json()["notes"] == "Closer price at Lidl"

    # Delete
    res = await client.delete(f"/api/products/{created['id']}")
    assert res.status_code == 204
    res = await client.get(f"/api/products/{created['id']}")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_product_search_filter(client: AsyncClient) -> None:
    for name in ["Whole Milk 1L", "Skim Milk 1L", "Sourdough 400g"]:
        await client.post("/api/products", json={"name": name, "category": "Dairy" if "Milk" in name else "Bakery"})

    res = await client.get("/api/products", params={"q": "milk"})
    assert res.status_code == 200
    items = res.json()
    assert {i["name"] for i in items} == {"Whole Milk 1L", "Skim Milk 1L"}

    res = await client.get("/api/products", params={"category": "Bakery"})
    assert res.status_code == 200
    items = res.json()
    assert len(items) == 1
    assert items[0]["name"] == "Sourdough 400g"


# ---- Stores -------------------------------------------------------------


@pytest.mark.asyncio
async def test_store_crud(client: AsyncClient) -> None:
    res = await client.post("/api/stores", json={
        "name": "Tesco",
        "kind": "both",
        "location_label": "Santry",
    })
    assert res.status_code == 201, res.text
    store = res.json()
    assert store["name"] == "Tesco"

    res = await client.patch(f"/api/stores/{store['id']}", json={"enabled": False})
    assert res.json()["enabled"] is False


# ---- Memberships --------------------------------------------------------


@pytest.mark.asyncio
async def test_membership_unique_per_store(client: AsyncClient) -> None:
    res = await client.post("/api/stores", json={"name": "Tesco", "kind": "both"})
    store_id = res.json()["id"]

    res = await client.post("/api/memberships", json={
        "store_id": store_id,
        "programme": "Clubcard",
        "account_label": "Primary",
    })
    assert res.status_code == 201

    res = await client.post("/api/memberships", json={
        "store_id": store_id,
        "programme": "Clubcard",
    })
    assert res.status_code == 409


@pytest.mark.asyncio
async def test_membership_404_when_store_missing(client: AsyncClient) -> None:
    res = await client.post("/api/memberships", json={
        "store_id": 99999,
        "programme": "Anything",
    })
    assert res.status_code == 404


# ---- Basket -------------------------------------------------------------


@pytest.mark.asyncio
async def test_basket_summary(client: AsyncClient) -> None:
    await client.post("/api/products", json={"name": "A", "category": "Dairy"})
    await client.post("/api/products", json={"name": "B", "category": "Bakery"})
    await client.post("/api/stores", json={"name": "Tesco", "kind": "both"})

    res = await client.get("/api/basket")
    assert res.status_code == 200
    data = res.json()
    assert data["count"] == 2
    assert data["stores"] == 1
    assert data["memberships"] == 0
    assert {i["name"] for i in data["items"]} == {"A", "B"}


# ---- Hunts --------------------------------------------------------------


@pytest.mark.asyncio
async def test_hunt_create_and_list(client: AsyncClient) -> None:
    res = await client.post("/api/hunts", json={
        "product_ids": [1, 2, 3],
        "store_ids": [10, 20],
    })
    assert res.status_code == 201
    hunt = res.json()
    assert hunt["status"] == "pending"
    assert hunt["product_ids"] == [1, 2, 3]

    res = await client.get("/api/hunts")
    assert res.status_code == 200
    assert len(res.json()) == 1

    res = await client.get(f"/api/hunts/{hunt['id']}")
    assert res.status_code == 200
    assert res.json()["id"] == hunt["id"]


@pytest.mark.asyncio
async def test_hunt_validates_non_empty(client: AsyncClient) -> None:
    res = await client.post("/api/hunts", json={"product_ids": [], "store_ids": [1]})
    assert res.status_code == 422
