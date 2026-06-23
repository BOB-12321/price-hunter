"""Pydantic schemas for API I/O.

Keep these separate from ORM models so we can:
- Hide internal columns from the wire
- Add validation that doesn't belong on the DB column
- Decouple API shape from storage shape (we can change DB without breaking clients)
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models import StoreKind


# ---- Shared ----------------------------------------------------------------


class ORMBase(BaseModel):
    """Common Pydantic v2 config: load attributes from ORM objects."""

    model_config = ConfigDict(from_attributes=True)


# ---- Products --------------------------------------------------------------


class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    brand: Optional[str] = Field(None, max_length=255)
    size: Optional[str] = Field(None, max_length=64)
    category: Optional[str] = Field(None, max_length=64)
    barcode: Optional[str] = Field(None, max_length=32)
    notes: Optional[str] = None


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    brand: Optional[str] = Field(None, max_length=255)
    size: Optional[str] = Field(None, max_length=64)
    category: Optional[str] = Field(None, max_length=64)
    barcode: Optional[str] = Field(None, max_length=32)
    notes: Optional[str] = None
    ingredients: Optional[str] = None
    off_id: Optional[str] = Field(None, max_length=64)
    nova_group: Optional[int] = Field(None, ge=1, le=4)


class ProductRead(ORMBase):
    id: int
    name: str
    brand: Optional[str] = None
    size: Optional[str] = None
    category: Optional[str] = None
    barcode: Optional[str] = None
    off_id: Optional[str] = None
    ingredients: Optional[str] = None
    nova_group: Optional[int] = None
    image_url: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime


# ---- Stores ----------------------------------------------------------------


class StoreBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    kind: StoreKind = StoreKind.IN_STORE
    location_label: Optional[str] = Field(None, max_length=128)
    online_url: Optional[str] = Field(None, max_length=1024)
    notes: Optional[str] = None
    enabled: bool = True


class StoreCreate(StoreBase):
    pass


class StoreUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=128)
    kind: Optional[StoreKind] = None
    location_label: Optional[str] = Field(None, max_length=128)
    online_url: Optional[str] = Field(None, max_length=1024)
    notes: Optional[str] = None
    enabled: Optional[bool] = None


class StoreRead(ORMBase):
    id: int
    name: str
    kind: StoreKind
    location_label: Optional[str] = None
    online_url: Optional[str] = None
    notes: Optional[str] = None
    enabled: bool
    created_at: datetime


# ---- Memberships -----------------------------------------------------------


class MembershipBase(BaseModel):
    programme: str = Field(..., min_length=1, max_length=64)
    account_label: Optional[str] = Field(None, max_length=128)
    notes: Optional[str] = None


class MembershipCreate(MembershipBase):
    store_id: int


class MembershipUpdate(BaseModel):
    programme: Optional[str] = Field(None, min_length=1, max_length=64)
    account_label: Optional[str] = Field(None, max_length=128)
    notes: Optional[str] = None
    registered_at: Optional[datetime] = None


class MembershipRead(ORMBase):
    id: int
    store_id: int
    programme: str
    account_label: Optional[str] = None
    registered_at: Optional[datetime] = None
    notes: Optional[str] = None


# ---- Basket ----------------------------------------------------------------
#
# A "basket" in Phase 2 is just the active list of products the user is
# currently comparing.  Real multi-basket support lands in a later phase
# if/when Robert needs trip-specific baskets ("Big weekly", "Quick top-up").


class BasketItemRead(ORMBase):
    """Lightweight product view as it appears in the basket list."""

    id: int
    name: str
    brand: Optional[str] = None
    size: Optional[str] = None
    category: Optional[str] = None
    in_basket: bool = True


class BasketSummary(BaseModel):
    """Combined response: current basket + counts."""

    items: list[ProductRead]
    count: int
    stores: int
    memberships: int


# ---- Hunt (placeholder) ----------------------------------------------------


class HuntRead(BaseModel):
    id: int
    status: str
    product_ids: list[int]
    store_ids: list[int]
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_at: datetime
