from __future__ import annotations

import json
from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="TOPICPILOT_",
        extra="ignore",
    )

    database_url: str = Field(
        default="postgresql+psycopg://topicpilot:topicpilot_local_only@localhost:5432/topicpilot",
        validation_alias="DATABASE_URL",
    )
    # Neon pooled connections are appropriate for the long-lived API process,
    # while Alembic should use a direct endpoint for migration DDL. The
    # migration setting is optional for local/legacy setups and falls back to
    # DATABASE_URL when it is not supplied.
    migration_database_url: str | None = Field(
        default=None,
        validation_alias="MIGRATION_DATABASE_URL",
    )
    cors_origins: Annotated[tuple[str, ...], NoDecode] = (
        "http://localhost:3000",
        "http://localhost:5173",
    )
    freshness_days: int = Field(default=3, ge=0, le=30)
    log_level: str = "INFO"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        if isinstance(value, str):
            raw = value.strip()
            if raw.startswith("["):
                decoded = json.loads(raw)
                if not isinstance(decoded, list):
                    raise ValueError("CORS origins JSON must be an array")
                return tuple(str(item).strip() for item in decoded if str(item).strip())
            return tuple(item.strip() for item in value.split(",") if item.strip())
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
