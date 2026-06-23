"""Tests for the seed script — verifies idempotency and seed content."""
from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy import select

from app import models
from app.db import Base, engine, session_scope
from app.seed import SEED_MEMBERSHIPS, SEED_STORES, run_seed


@pytest_asyncio.fixture(autouse=True)
async def _reset_schema():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_seed_inserts_expected_stores():
    result = await run_seed()
    assert result["stores_added"] == len(SEED_STORES)
    assert result["memberships_added"] == len(SEED_MEMBERSHIPS)


@pytest.mark.asyncio
async def test_seed_is_idempotent():
    first = await run_seed()
    second = await run_seed()
    assert first["stores_added"] > 0
    assert second["stores_added"] == 0
    assert second["memberships_added"] == 0


@pytest.mark.asyncio
async def test_seed_includes_roberts_memberships():
    await run_seed()
    async with session_scope() as session:
        stores = (await session.execute(select(models.Store))).scalars().all()
        store_by_name = {s.name: s for s in stores}
        tesco_id = store_by_name["Tesco"].id
        boots_id = store_by_name["Boots"].id

        memberships = (await session.execute(
            select(models.Membership).where(
                models.Membership.store_id.in_([tesco_id, boots_id])
            )
        )).scalars().all()

    programmes = {m.programme for m in memberships}
    assert "Clubcard" in programmes
    assert "Advantage Card" in programmes
