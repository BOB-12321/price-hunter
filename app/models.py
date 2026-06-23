"""ORM models.  Phase 1 ships only the minimum needed to confirm the
schema migration path; Phase 2 expands the rest.

Tables defined here:
- products     — items in the user's basket (and candidates to compare)
- stores       — retailers in scope
- memberships  — loyalty programmes the user belongs to
- prices       — captured price points, with member-price / unit-price columns
- receipts     — uploaded receipt images and their parsed content
- hunts        — runs of a price comparison across N products × M stores
- watchlist    — target prices; alerts triggered when matched
"""
from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class StoreKind(str, enum.Enum):
    """Whether a store has an online shop, an in-store presence, or both."""

    ONLINE = "online"
    IN_STORE = "in_store"
    BOTH = "both"
    MANUAL = "manual"  # Aldi Specialbuys, Londis — no online shop


class HuntStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    brand: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    size: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    barcode: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True)
    off_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    ingredients: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    nova_group: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    prices: Mapped[list["Price"]] = relationship(back_populates="product")


class Store(Base):
    __tablename__ = "stores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    kind: Mapped[StoreKind] = mapped_column(
        Enum(StoreKind, name="store_kind"),
        nullable=False,
        default=StoreKind.IN_STORE,
    )
    location_label: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    online_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    prices: Mapped[list["Price"]] = relationship(back_populates="store")
    memberships: Mapped[list["Membership"]] = relationship(back_populates="store")


class Membership(Base):
    __tablename__ = "memberships"
    __table_args__ = (
        UniqueConstraint("store_id", "programme", name="uq_memberships_store_programme"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    store_id: Mapped[int] = mapped_column(
        ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True
    )
    programme: Mapped[str] = mapped_column(String(64), nullable=False)
    account_label: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    registered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    store: Mapped[Store] = relationship(back_populates="memberships")


class Price(Base):
    __tablename__ = "prices"
    __table_args__ = (
        # One captured price per (product, store) at a moment in time; later
        # we may want a unique constraint that ignores second-resolution
        # duplicates, but for now capture everything.
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    store_id: Mapped[int] = mapped_column(
        ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True
    )
    price: Mapped[float] = mapped_column(Float, nullable=False)
    member_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    unit_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="EUR")
    in_stock: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    raw: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    product: Mapped[Product] = relationship(back_populates="prices")
    store: Mapped[Store] = relationship(back_populates="prices")


class Receipt(Base):
    __tablename__ = "receipts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    store_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("stores.id", ondelete="SET NULL"), nullable=True
    )
    image_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    total: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    parsed: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class Hunt(Base):
    __tablename__ = "hunts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    status: Mapped[HuntStatus] = mapped_column(
        Enum(HuntStatus, name="hunt_status"),
        nullable=False,
        default=HuntStatus.PENDING,
    )
    product_ids: Mapped[list[int]] = mapped_column(JSON, nullable=False, default=list)
    store_ids: Mapped[list[int]] = mapped_column(JSON, nullable=False, default=list)
    results: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Watchlist(Base):
    __tablename__ = "watchlist"
    __table_args__ = (
        UniqueConstraint("product_id", "store_id", name="uq_watchlist_product_store"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    store_id: Mapped[int] = mapped_column(
        ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_price: Mapped[float] = mapped_column(Float, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
