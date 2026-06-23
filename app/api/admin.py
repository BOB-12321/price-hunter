"""Admin endpoint for seeding the database.

Gated by a simple token header (X-Seed-Token) matching
``settings.admin_token``.  In Phase 2 the token is a static value from
``.env``; Phase 7+ may upgrade to a real auth scheme.
"""
from __future__ import annotations

import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.config import settings
from app.seed import run_seed

router = APIRouter(prefix="/api/admin", tags=["admin"])


def _check_token(x_seed_token: Annotated[str | None, Header()] = None) -> None:
    expected = settings.admin_token
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin token not configured on the server.",
        )
    if not x_seed_token or not secrets.compare_digest(x_seed_token, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin token."
        )


@router.post("/seed", dependencies=[Depends(_check_token)])
async def seed() -> dict:
    """Run the seed script.  Idempotent."""
    result = await run_seed()
    return {"status": "ok", **result}
