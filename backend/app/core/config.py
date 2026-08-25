"""
app/core/config.py
──────────────────
Centralised application configuration loaded via pydantic-settings.

All settings can be overridden by environment variables or a .env file.
No secrets are hard-coded here.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import AnyUrl, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide settings resolved from env / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        # Ignore extra env variables — important in shared environments.
        extra="ignore",
    )

    # ── Application ───────────────────────────────────────────────────────────
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "INSECURE_CHANGE_ME_IN_PRODUCTION"

    # ── Database ──────────────────────────────────────────────────────────────
    # Default: in-process SQLite for local development.
    # Replace with postgresql+asyncpg://... for staging/production.
    DATABASE_URL: str = "sqlite+aiosqlite:///./cadastravision.db"

    # ── CORS ──────────────────────────────────────────────────────────────────
    # Stored as a comma-separated string so it can be set via a single env var.
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # ── Logging ───────────────────────────────────────────────────────────────
    LOG_LEVEL: str = "DEBUG"

    # ── Derived helpers ───────────────────────────────────────────────────────
    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        if self.ENVIRONMENT == "production":
            if self.SECRET_KEY == "INSECURE_CHANGE_ME_IN_PRODUCTION" or len(self.SECRET_KEY) < 16:
                raise ValueError("Insecure or default SECRET_KEY is prohibited in production environment.")
            if self.DEBUG:
                raise ValueError("DEBUG mode must be False in production environment.")
        return self

    @property
    def cors_origins_list(self) -> list[str]:
        """Return CORS_ORIGINS as a Python list."""
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return the cached Settings singleton.

    Using ``@lru_cache`` means the .env file is parsed only once at startup.
    Override in tests with:

        app.dependency_overrides[get_settings] = lambda: Settings(...)
    """
    return Settings()
