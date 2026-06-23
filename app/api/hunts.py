"""Hunt endpoints.

Phase 2 ships a read-only view of hunts (the actual price-pull orchestration
lands in Phase 3 with the first real store adapter).  We expose:

- GET    /api/hunts          list hunts
- POST   /api/hunts          create a pending hunt for a product × store set
- GET    /api/hunts/{id}     retrieve a single hunt with results

The status field is what the UI uses to drive a live progress bar.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.db import get_session

router = APIRouter(prefix="/api/hunts", tags=["hunts"])


class HuntCreate(BaseModel):
    """Request body for creating a new hunt."""

    product_ids: list[int] = Field(..., min_length=1)
    store_ids: list[int] = Field(..., min_length=1)


@router.get("", response_model=list[schemas.HuntRead])
async def list_hunts(
    session: AsyncSession = Depends(get_session),
    limit: int = 20,
) -> list[models.Hunt]:
    stmt = (
        select(models.Hunt)
        .order_by(models.Hunt.created_at.desc())
        .limit(limit)
    )
    rows = (await session.execute(stmt)).scalars().all()
    return list(rows)


@router.post("", response_model=schemas.HuntRead, status_code=status.HTTP_201_CREATED)
async def create_hunt(
    body: HuntCreate,
    session: AsyncSession = Depends(get_session),
) -> models.Hunt:
    """Create a pending hunt.  Phase 3 will trigger the worker that runs it."""
    hunt = models.Hunt(
        status=models.HuntStatus.PENDING,
        product_ids=body.product_ids,
        store_ids=body.store_ids,
    )
    session.add(hunt)
    await session.commit()
    await session.refresh(hunt)
    return hunt


@router.get("/{hunt_id}", response_model=schemas.HuntRead)
async def get_hunt(
    hunt_id: int,
    session: AsyncSession = Depends(get_session),
) -> models.Hunt:
    hunt = await session.get(models.Hunt, hunt_id)
    if hunt is None:
        raise HTTPException(status_code=404, detail="Hunt not found")
    return hunt
