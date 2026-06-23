"""Loyalty programme / membership endpoints.

In Phase 2 these are simple CRUD.  In Phase 5 they will gain
``member_price`` support — Tesco Clubcard Prices, Boots Advantage
multipliers, etc.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.db import get_session

router = APIRouter(prefix="/api/memberships", tags=["memberships"])


@router.get("", response_model=list[schemas.MembershipRead])
async def list_memberships(
    session: AsyncSession = Depends(get_session),
    store_id: int | None = None,
) -> list[models.Membership]:
    stmt = select(models.Membership).order_by(models.Membership.id)
    if store_id is not None:
        stmt = stmt.where(models.Membership.store_id == store_id)
    rows = (await session.execute(stmt)).scalars().all()
    return list(rows)


@router.post("", response_model=schemas.MembershipRead, status_code=status.HTTP_201_CREATED)
async def create_membership(
    body: schemas.MembershipCreate,
    session: AsyncSession = Depends(get_session),
) -> models.Membership:
    store = await session.get(models.Store, body.store_id)
    if store is None:
        raise HTTPException(status_code=404, detail="Store not found")
    membership = models.Membership(**body.model_dump())
    session.add(membership)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=409,
            detail="A membership for this store + programme already exists",
        )
    await session.refresh(membership)
    return membership


@router.delete("/{membership_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_membership(
    membership_id: int,
    session: AsyncSession = Depends(get_session),
) -> Response:
    membership = await session.get(models.Membership, membership_id)
    if membership is None:
        raise HTTPException(status_code=404, detail="Membership not found")
    await session.delete(membership)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
