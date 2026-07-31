from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="TOPICPILOT_",
        extra="ignore",
    )

    database_url: str = Field(
        default="postgresql+psycopg://topicpilot:topicpilot@localhost:5432/topicpilot",
        validation_alias="DATABASE_URL",
    )
    cors_origins: tuple[str, ...] = ("http://localhost:3000", "http://localhost:5173")
    freshness_days: int = Field(default=3, ge=0, le=30)
    log_level: str = "INFO"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return tuple(item.strip() for item in value.split(",") if item.strip())
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
