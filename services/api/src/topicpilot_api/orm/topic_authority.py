"""Governed Topic authority activation audit records."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, CreatedAtMixin, IdentityMixin


class TopicAuthorityActivation(Base, IdentityMixin, CreatedAtMixin):
    """Append-only lineage for one successfully activated authority artifact."""

    __tablename__ = "topic_authority_activations"
    __table_args__ = (
        UniqueConstraint("activation_version", name="uq_topic_authority_activation_version"),
        CheckConstraint(
            "status IN ('ACTIVE', 'SUPERSEDED')",
            name="topic_authority_activation_status",
        ),
        CheckConstraint(
            "length(artifact_sha256) = 64 AND length(readback_sha256) = 64",
            name="topic_authority_activation_hashes",
        ),
    )

    activation_version: Mapped[str] = mapped_column(String(96), nullable=False)
    artifact_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    source_master_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    source_revision: Mapped[str] = mapped_column(String(64), nullable=False)
    target_environment: Mapped[str] = mapped_column(String(32), nullable=False)
    target_database: Mapped[str] = mapped_column(String(128), nullable=False)
    operator_id: Mapped[str] = mapped_column(String(128), nullable=False)
    approval_reference: Mapped[str] = mapped_column(String(256), nullable=False)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    previous_activation_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("topicpilot.topic_authority_activations.id", ondelete="RESTRICT")
    )
    active_parent_count: Mapped[int] = mapped_column(Integer, nullable=False)
    active_leaf_count: Mapped[int] = mapped_column(Integer, nullable=False)
    lifecycle_scope_count: Mapped[int] = mapped_column(Integer, nullable=False)
    readback_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    artifact: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)


__all__ = ["TopicAuthorityActivation"]
