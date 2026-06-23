"""FastAPI application entrypoint.

Wires up routers, static file serving, lifecycle events (DB init), and a
healthcheck endpoint.  Phase 1 ships the healthcheck and the mobile-first
landing page; Phase 2 adds CRUD for products, stores, memberships, basket,
and hunts.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.api import admin, basket, hunts, memberships, products, stores
from app.config import settings
from app.db import init_db

logger = logging.getLogger("pricehunter")
logging.basicConfig(
    level=logging.INFO if not settings.is_production else logging.WARNING,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

WEB_DIR = Path(__file__).parent / "web"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup/shutdown hooks.  Currently: create tables if missing."""
    logger.info("Price Hunter %s starting (env=%s)", __version__, settings.app_env)
    await init_db()
    logger.info("DB schema ready")
    yield
    logger.info("Price Hunter shutting down")


app = FastAPI(
    title="Price Hunter",
    version=__version__,
    description=(
        "Personal shopping price-comparison scout for Dublin Northside. "
        "Telegram-first, mobile-first, Tailscale-only."
    ),
    lifespan=lifespan,
)


# ---- Healthcheck ---------------------------------------------------------


@app.get("/healthz", tags=["meta"])
async def healthz() -> JSONResponse:
    """Liveness/readiness check used by Docker HEALTHCHECK and uptime monitors."""
    return JSONResponse(
        {
            "status": "ok",
            "version": __version__,
            "env": settings.app_env,
        }
    )


# ---- Static UI -----------------------------------------------------------


# Mount /static for assets (CSS, JS, images).  The index page is served
# directly at / to avoid a trailing-slash redirect on phones.
app.mount(
    "/static",
    StaticFiles(directory=str(WEB_DIR)),
    name="static",
)


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    """Mobile-first landing page."""
    return FileResponse(str(WEB_DIR / "index.html"))


# ---- API routers ---------------------------------------------------------


app.include_router(products.router)
app.include_router(stores.router)
app.include_router(memberships.router)
app.include_router(basket.router)
app.include_router(hunts.router)
app.include_router(admin.router)


@app.get("/api", tags=["meta"])
async def api_root() -> JSONResponse:
    """Friendly landing for the API.  Lists live endpoints for quick exploration."""
    return JSONResponse(
        {
            "service": "price-hunter",
            "version": __version__,
            "docs": "/docs",
            "endpoints": {
                "healthz": "/healthz",
                "ui": "/",
                "products": "/api/products",
                "stores": "/api/stores",
                "memberships": "/api/memberships",
                "basket": "/api/basket",
                "hunts": "/api/hunts",
            },
        }
    )
