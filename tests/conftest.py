"""Test-suite configuration.  Runs before any test module is imported.

Sets sane defaults so tests don't accidentally hit the docker Postgres
or leak the production ADMIN_TOKEN.
"""
from __future__ import annotations

import os

# Pin a fast, isolated database BEFORE app modules import.
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("ADMIN_TOKEN", "test-token-xyz")
