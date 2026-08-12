from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, CreatedAtMixin, IdentityMixin


class LegacyImportRun(Base, IdentityMixin, CreatedAtMixin):
    __tablename__ = "legacy_import_runs"
    # export_id identifies immutable source content; id identifies each attempt.
    __table_args__ = (Index("ix_legacy_import_runs_export_id", "export_id"),)
    export_id: Mapped[str] = mapped_column(String(160), nullable=False)
    contract_version: Mapped[str] = mapped_column(String(64), nullable=False)
    mapping_policy_version: Mapped[str] = mapped_column(String(64), nullable=False)
    migration_baseline: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    records: Mapped[list[LegacyImportRecord]] = relationship(back_populates="run")
    artifacts: Mapped[list[LegacyImportArtifact]] = relationship(back_populates="run")


class LegacyImportArtifact(Base, IdentityMixin):
    __tablename__ = "legacy_import_artifacts"
    __table_args__ = (
        UniqueConstraint("run_id", "filename", name="uq_legacy_import_artifacts_run_file"),
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("topicpilot.legacy_import_runs.id", ondelete="CASCADE"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    row_count: Mapped[int] = mapped_column(nullable=False)
    run: Mapped[LegacyImportRun] = relationship(back_populates="artifacts")


class LegacyImportRecord(Base, IdentityMixin):
    __tablename__ = "legacy_import_records"
    __table_args__ = (
        UniqueConstraint("run_id", "entity", "stable_key", name="uq_legacy_import_records_key"),
        Index("ix_legacy_import_records_lookup", "entity", "stable_key", "canonical_payload_hash"),
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("topicpilot.legacy_import_runs.id", ondelete="CASCADE"), nullable=False
    )
    entity: Mapped[str] = mapped_column(String(64), nullable=False)
    stable_key: Mapped[str] = mapped_column(String(512), nullable=False)
    canonical_payload_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    source_filename: Mapped[str | None] = mapped_column(String(255))
    source_row: Mapped[int | None] = mapped_column()
    outcome: Mapped[str] = mapped_column(String(32), nullable=False)
    target_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    run: Mapped[LegacyImportRun] = relationship(back_populates="records")
