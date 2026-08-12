"""Phase 3.4-002 identity domain."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0014_phase3_4_002_identity_domain"
down_revision = "0013_phase2_analytics_views"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # This schema is shared by the V2 domain tables.  Own its creation here
    # so a fresh database can apply this revision without out-of-band setup.
    op.execute("CREATE SCHEMA IF NOT EXISTS topicpilot")

    op.create_table("markets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(32), nullable=False), sa.Column("name", sa.String(160), nullable=False),
        sa.Column("exchange_code", sa.String(32)), sa.Column("timezone", sa.String(64), nullable=False),
        sa.Column("calendar_code", sa.String(64)), sa.Column("valid_from", sa.Date()), sa.Column("valid_to", sa.Date()),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("valid_to IS NULL OR valid_from IS NULL OR valid_to >= valid_from", name="ck_markets_valid_range"),
        sa.UniqueConstraint("code", name="uq_markets_code"), schema="topicpilot")
    op.create_table("instruments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("market_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("instrument_code", sa.String(64), nullable=False), sa.Column("name", sa.String(160)),
        sa.Column("instrument_type", sa.String(32), nullable=False), sa.Column("currency", sa.String(3)),
        sa.Column("valid_from", sa.Date()), sa.Column("valid_to", sa.Date()),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["market_id"], ["topicpilot.markets.id"], ondelete="RESTRICT", name="fk_instruments_market_id_markets"),
        sa.CheckConstraint("valid_to IS NULL OR valid_from IS NULL OR valid_to >= valid_from", name="ck_instruments_valid_range"),
        sa.UniqueConstraint("market_id", "instrument_code", name="uq_instruments_market_code"), schema="topicpilot")
    op.create_table("security_identities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("instrument_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("market_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("identifier_namespace", sa.String(64), nullable=False), sa.Column("identifier_value", sa.String(128), nullable=False),
        sa.Column("resolution_status", sa.String(32), nullable=False),
        sa.Column("valid_from", sa.Date(), nullable=False), sa.Column("valid_to", sa.Date()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["instrument_id"], ["topicpilot.instruments.id"], ondelete="RESTRICT", name="fk_instrument_symbols_instrument_id_instruments"),
        sa.ForeignKeyConstraint(["market_id"], ["topicpilot.markets.id"], ondelete="RESTRICT", name="fk_instrument_symbols_market_id_markets"),
        sa.CheckConstraint("valid_to IS NULL OR valid_to >= valid_from", name="ck_instrument_symbols_valid_range"),
        sa.CheckConstraint("valid_to IS NULL OR valid_to >= valid_from", name="ck_security_identities_valid_range"),
        sa.UniqueConstraint("market_id", "identifier_namespace", "identifier_value", "valid_from", name="uq_security_identities_effective"), schema="topicpilot")


def downgrade() -> None:
    op.drop_table("security_identities", schema="topicpilot")
    op.drop_table("instruments", schema="topicpilot")
    op.drop_table("markets", schema="topicpilot")
