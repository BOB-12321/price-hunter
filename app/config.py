"""Application configuration loaded from environment variables.

Single source of truth for paths, network, and third-party credentials.  Read
once at import time; tests can override via environment before importing.
"""
from __future__ import annotations

import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 3016

    # Storage
    data_dir: Path = Path("/app/data")

    # Database — asyncpg DSN
    database_url: str = (
        "postgresql+asyncpg://pricehunter:change_me_in_prod@db:5432/pricehunter"
    )

    # Telegram
    telegram_bot_token: str = ""
    telegram_home_chat_id: str = ""

    # Open Food Facts
    off_api_url: str = "https://world.openfoodfacts.org"

    # Admin token (X-Seed-Token).  Generated in .env; rotate by replacing it
    # and restarting the app.  Phase 2 only gates the /api/admin/seed
    # endpoint; later phases may add more admin surfaces.
    admin_token: str = ""

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() in {"prod", "production"}


settings = Settings()
settings.data_dir.mkdir(parents=True, exist_ok=True)
