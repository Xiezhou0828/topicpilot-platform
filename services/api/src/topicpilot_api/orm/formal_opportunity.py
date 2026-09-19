"""Formal Opportunity publication envelope and persisted readback model."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Date,
    DateTime,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, CreatedAtMixin, IdentityMixin, UpdatedAtMixin


class FormalOpportunityPublication(Base, IdentityMixin, CreatedAtMixin, UpdatedAtMixin):
    """One immutable formal Opportunity page publication.

    The payload is provider-owned and is validated against the public formal
    API contract before it is written.  Shadow, research, and fixture data are
    never copied into this table.
    """

    __tablename__ = "formal_opportunity_publications"
    __table_args__ = (
        UniqueConstraint("publication_key", name="uq_formal_opportunity_publication_key"),
        CheckConstraint(
            "publication_state IN ('PUBLISHED', 'EMPTY', 'DEFERRED', 'UNAVAILABLE', 'SUPERSEDED')",
            name="ck_formal_opportunity_publication_state",
        ),
        Index(
            "ix_formal_opportunity_publication_lookup",
            "as_of",
            "publication_state",
            "created_at",
        ),
    )

    as_of: Mapped[date] = mapped_column(Date, nullable=False)
    publication_state: Mapped[str] = mapped_column(String(24), nullable=False)
    authority_version: Mapped[str] = mapped_column(String(96), nullable=False)
    contract_version: Mapped[str] = mapped_column(String(96), nullable=False)
    publication_key: Mapped[str] = mapped_column(String(256), nullable=False)
    provider_version: Mapped[str] = mapped_column(String(96), nullable=False)
    source_artifact_id: Mapped[str] = mapped_column(String(256), nullable=False)
    source_artifact_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    lineage_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    page_payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), nullable=False
    )
    detail_payloads: Mapped[dict[str, Any]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), nullable=False
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    diagnostic_reason: Mapped[str | None] = mapped_column(Text)


__all__ = ["FormalOpportunityPublication"]
