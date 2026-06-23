"""Store CRUD endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.db import get_session

router = APIRouter(prefix="/api/stores", tags=["stores"])


@router.get("", response_model=list[schemas.StoreRead])
async def list_stores(
    session: AsyncSession = Depends(get_session),
    enabled: bool | None = None,
) -> list[models.Store]:
    stmt = select(models.Store).order_by(models.Store.name)
    if enabled is not None:
        stmt = stmt.where(models.Store.enabled == enabled)
    rows = (await session.execute(stmt)).scalars().all()
    return list(rows)


@router.post("", response_model=schemas.StoreRead, status_code=status.HTTP_201_CREATED)
async def create_store(
    body: schemas.StoreCreate,
    session: AsyncSession = Depends(get_session),
) -> models.Store:
    store = models.Store(**body.model_dump())
    session.add(store)
    await session.commit()
    await session.refresh(store)
    return store


@router.get("/{store_id}", response_model=schemas.StoreRead)
async def get_store(
    store_id: int,
    session: AsyncSession = Depends(get_session),
) -> models.Store:
    store = await session.get(models.Store, store_id)
    if store is None:
        raise HTTPException(status_code=404, detail="Store not found")
    return store


@router.patch("/{store_id}", response_model=schemas.StoreRead)
async def update_store(
    store_id: int,
    body: schemas.StoreUpdate,
    session: AsyncSession = Depends(get_session),
) -> models.Store:
    store = await session.get(models.Store, store_id)
    if store is None:
        raise HTTPException(status_code=404, detail="Store not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(store, field, value)
    await session.commit()
    await session.refresh(store)
    return store


@router.delete("/{store_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_store(
    store_id: int,
    session: AsyncSession = Depends(get_session),
) -> Response:
    store = await session.get(models.Store, store_id)
    if store is None:
        raise HTTPException(status_code=404, detail="Store not found")
    await session.delete(store)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
