"""Async database engine and session helpers."""
from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for ORM models."""


# echo=False keeps logs quiet; flip to True while debugging query issues.
# Pool sizing only applies to real RDBMS backends; SQLite falls back to
# StaticPool, which ignores pool_size / max_overflow (a hard error otherwise).
_engine_kwargs: dict = {
    "echo": False,
    "pool_pre_ping": True,
}
if not settings.database_url.startswith("sqlite"):
    _engine_kwargs.update({"pool_size": 5, "max_overflow": 10})

engine = create_async_engine(settings.database_url, **_engine_kwargs)

SessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine, expire_on_commit=False
)


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency yielding a transactional session."""
    async with SessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    """Context manager variant for non-FastAPI code paths (background jobs, scripts)."""
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Create tables if they don't exist.  Called at app startup.

    Real schema migrations will arrive with Phase 2 (Alembic); this
    bootstrap keeps the Phase 1 skeleton self-contained.
    """
    # Importing here avoids a circular reference: Base must exist before
    # models import it, and models import Base via this module.
    from app import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
