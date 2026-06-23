"""Basket summary endpoint.

Phase 2 returns the active product list and useful counts.  Once the
dedicated ``basket_items`` table lands in Phase 3 this becomes a richer
view (sorted by recency, grouped by category, with a per-product last
purchased price from receipts).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.db import get_session

router = APIRouter(prefix="/api/basket", tags=["basket"])


@router.get("", response_model=schemas.BasketSummary)
async def get_basket(session: AsyncSession = Depends(get_session)) -> schemas.BasketSummary:
    products = (
        (await session.execute(select(models.Product).order_by(models.Product.name)))
        .scalars()
        .all()
    )
    store_count = (
        await session.execute(select(func.count(models.Store.id)))
    ).scalar_one()
    membership_count = (
        await session.execute(select(func.count(models.Membership.id)))
    ).scalar_one()
    return schemas.BasketSummary(
        items=[schemas.ProductRead.model_validate(p) for p in products],
        count=len(products),
        stores=store_count,
        memberships=membership_count,
    )
