"""Seed the database with the Dublin Northside store list and Robert's
memberships.

Run with ``python -m app.seed`` from the project root, or via the
``/api/admin/seed`` HTTP endpoint (gated by the X-Seed-Token header for
safety).  Idempotent — running it twice is a no-op.
"""
from __future__ import annotations

import logging
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.db import session_scope

logger = logging.getLogger("pricehunter.seed")


# Dublin Northside store list.  ``kind`` reflects whether we expect to pull
# real prices (BOTH/IN_STORE) or only manual entry (MANUAL for Aldi
# Specialbuys, Londis).
SEED_STORES: list[dict] = [
    {
        "name": "Tesco",
        "kind": models.StoreKind.BOTH,
        "location_label": "Dublin Northside (Santry, Swords, Malahide, Baldoyle, Portmarnock)",
        "online_url": "https://www.tesco.ie",
        "notes": "Clubcard pricing applied where visible publicly.",
    },
    {
        "name": "SuperValu",
        "kind": models.StoreKind.BOTH,
        "location_label": "Dublin Northside",
        "online_url": "https://shop.supervalu.ie",
        "notes": "Real Rewards.  Prices vary by store; default to Northside.",
    },
    {
        "name": "Dunnes Stores",
        "kind": models.StoreKind.BOTH,
        "location_label": "Dublin Northside",
        "online_url": "https://www.dunnesstores.com",
        "notes": "Value Club pricing visible online.",
    },
    {
        "name": "Aldi",
        "kind": models.StoreKind.MANUAL,
        "location_label": "Dublin Northside",
        "online_url": "https://www.aldi.ie",
        "notes": "Manual entry for weekly grocery range; Specialbuys scraped weekly.",
    },
    {
        "name": "Lidl",
        "kind": models.StoreKind.BOTH,
        "location_label": "Dublin Northside",
        "online_url": "https://www.lidl.ie",
        "notes": "Lidl Plus pricing where visible.",
    },
    {
        "name": "Londis",
        "kind": models.StoreKind.MANUAL,
        "location_label": "Dublin Northside",
        "online_url": None,
        "notes": "Franchise model; no online shop.  Manual price entry only.",
    },
    {
        "name": "Boots",
        "kind": models.StoreKind.BOTH,
        "location_label": "Dublin Northside",
        "online_url": "https://www.boots.ie",
        "notes": "Advantage Card (4 pts per €1).",
    },
    # Online-only retailers in scope for cleaning / hygiene / vitamins.
    {
        "name": "Amazon.ie",
        "kind": models.StoreKind.ONLINE,
        "location_label": "Online",
        "online_url": "https://www.amazon.ie",
        "notes": "Cleaning / hygiene / vitamins fallback.",
    },
    {
        "name": "Boots.ie",
        "kind": models.StoreKind.ONLINE,
        "location_label": "Online",
        "online_url": "https://www.boots.ie",
        "notes": "Separate from physical Boots for online-only prices.",
    },
]


SEED_MEMBERSHIPS: list[dict] = [
    # Robert's confirmed memberships
    {"store_name": "Tesco", "programme": "Clubcard", "account_label": "Primary"},
    {"store_name": "Boots", "programme": "Advantage Card", "account_label": "Primary"},
    # Robert plans to register — add placeholders so the UI reminds him.
    {"store_name": "SuperValu", "programme": "Real Rewards", "account_label": "TODO: register"},
    {"store_name": "Dunnes Stores", "programme": "Value Club", "account_label": "TODO: register"},
    {"store_name": "Lidl", "programme": "Lidl Plus", "account_label": "TODO: install app"},
]


async def _seed_stores(session: AsyncSession) -> int:
    inserted = 0
    for spec in SEED_STORES:
        existing = (
            await session.execute(
                select(models.Store).where(models.Store.name == spec["name"])
            )
        ).scalar_one_or_none()
        if existing is not None:
            continue
        session.add(models.Store(**spec))
        inserted += 1
    return inserted


async def _seed_memberships(session: AsyncSession) -> int:
    inserted = 0
    for spec in SEED_MEMBERSHIPS:
        store = (
            await session.execute(
                select(models.Store).where(models.Store.name == spec["store_name"])
            )
        ).scalar_one_or_none()
        if store is None:
            logger.warning("Skipping membership for unknown store %s", spec["store_name"])
            continue
        existing = (
            await session.execute(
                select(models.Membership).where(
                    models.Membership.store_id == store.id,
                    models.Membership.programme == spec["programme"],
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            continue
        session.add(
            models.Membership(
                store_id=store.id,
                programme=spec["programme"],
                account_label=spec.get("account_label"),
            )
        )
        inserted += 1
    return inserted


async def run_seed() -> dict[str, int]:
    """Seed stores + memberships; return counts of newly inserted rows."""
    async with session_scope() as session:
        stores_added = await _seed_stores(session)
        memberships_added = await _seed_memberships(session)
    return {"stores_added": stores_added, "memberships_added": memberships_added}


if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.INFO)
    result = asyncio.run(run_seed())
    print(result)
