"""Product CRUD endpoints.

Phase 2: simple list/create/read/update/delete.  The basket is the set of
products where ``deleted_at IS NULL`` AND the user has marked them as in
the basket (we use a soft-delete pattern in Phase 3 when the basket table
arrives).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.db import get_session

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("", response_model=list[schemas.ProductRead])
async def list_products(
    session: AsyncSession = Depends(get_session),
    q: str | None = None,
    category: str | None = None,
    in_basket: bool | None = None,
) -> list[models.Product]:
    """List products, optionally filtered by name fragment or category.

    ``in_basket`` is a placeholder flag for Phase 3 — until we have a
    dedicated basket table, the UI shows everything; the flag is wired
    but treated as "include all".
    """
    stmt = select(models.Product).order_by(models.Product.name)
    if q:
        stmt = stmt.where(models.Product.name.ilike(f"%{q}%"))
    if category:
        stmt = stmt.where(models.Product.category == category)
    rows = (await session.execute(stmt)).scalars().all()
    return list(rows)


@router.post("", response_model=schemas.ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(
    body: schemas.ProductCreate,
    session: AsyncSession = Depends(get_session),
) -> models.Product:
    product = models.Product(**body.model_dump())
    session.add(product)
    await session.commit()
    await session.refresh(product)
    return product


@router.get("/{product_id}", response_model=schemas.ProductRead)
async def get_product(
    product_id: int,
    session: AsyncSession = Depends(get_session),
) -> models.Product:
    product = await session.get(models.Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.patch("/{product_id}", response_model=schemas.ProductRead)
async def update_product(
    product_id: int,
    body: schemas.ProductUpdate,
    session: AsyncSession = Depends(get_session),
) -> models.Product:
    product = await session.get(models.Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    await session.commit()
    await session.refresh(product)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_product(
    product_id: int,
    session: AsyncSession = Depends(get_session),
) -> Response:
    product = await session.get(models.Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    await session.delete(product)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
