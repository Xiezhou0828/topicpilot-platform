"""Phase 3.5-001B canonical observation schema."""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0019_phase3_5_001b_canonical_observations"
down_revision = "0018_phase3_4_006_observation_timeline"
branch_labels = None
depends_on = None
UUID = lambda n, **kw: sa.Column(n, postgresql.UUID(as_uuid=True), **kw)
STR = lambda n, length, **kw: sa.Column(n, sa.String(length), **kw)
NUM = lambda n: sa.Column(n, sa.Numeric(38, 18))
JSON = lambda n: sa.Column(n, postgresql.JSONB())

def upgrade():
    op.create_table("canonical_observations",
        UUID("id", primary_key=True), UUID("timeline_entry_id", nullable=False), UUID("instrument_id", nullable=False), UUID("source_id", nullable=False), UUID("raw_observation_id", nullable=False),
        STR("session_code",64,nullable=False), STR("timezone_name",64,nullable=False), STR("calendar_code",64,nullable=False), STR("family_code",32,nullable=False),
        sa.Column("observed_at",sa.DateTime(timezone=True),nullable=False), sa.Column("received_at",sa.DateTime(timezone=True),nullable=False), sa.Column("retrieved_at",sa.DateTime(timezone=True),nullable=False),
        STR("source_field_path",512), STR("ordering_key",256,nullable=False), STR("normalization_contract_version",64,nullable=False), STR("mapping_policy_version",64,nullable=False), STR("reference_data_version",64,nullable=False),
        STR("quality_state",32,nullable=False,server_default="ACCEPTED"), JSON("quality_warnings"), JSON("validation_summary"), STR("disposition",64), UUID("supersedes_id"), STR("content_hash",128,nullable=False), STR("idempotency_key",256,nullable=False),
        sa.Column("created_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()), sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["timeline_entry_id"],["topicpilot.observation_timeline_entries.id"],ondelete="RESTRICT"), sa.ForeignKeyConstraint(["instrument_id"],["topicpilot.instruments.id"],ondelete="RESTRICT"), sa.ForeignKeyConstraint(["source_id"],["topicpilot.market_data_sources.id"],ondelete="RESTRICT"), sa.ForeignKeyConstraint(["raw_observation_id"],["topicpilot.raw_market_observations.id"],ondelete="RESTRICT"), sa.ForeignKeyConstraint(["supersedes_id"],["topicpilot.canonical_observations.id"],ondelete="RESTRICT"),
        sa.UniqueConstraint("idempotency_key",name="uq_canonical_observations_idempotency"), sa.CheckConstraint("family_code IN ('PRICE','VOLUME','QUOTE','TRADING_STATUS')",name="ck_canonical_observations_family"), sa.CheckConstraint("quality_state IN ('ACCEPTED','INCOMPLETE','AMBIGUOUS','CONFLICTING','QUARANTINED','REJECTED')",name="ck_canonical_observations_quality"), sa.CheckConstraint("supersedes_id IS NULL OR supersedes_id <> id",name="ck_canonical_observations_no_self_supersession"), sa.CheckConstraint("length(normalization_contract_version)>0 AND length(mapping_policy_version)>0 AND length(reference_data_version)>0 AND length(content_hash)>0 AND length(idempotency_key)>0",name="ck_canonical_observations_nonempty_lineage"), schema="topicpilot")
    detail = {
      "canonical_price_observations": [NUM("open"),NUM("high"),NUM("low"),NUM("close"),NUM("last"),NUM("vwap"),STR("price_currency_code",3,nullable=False),sa.Column("price_scale",sa.SmallInteger,nullable=False),STR("adjustment_state",16,nullable=False,server_default="UNKNOWN"),JSON("price_context")],
      "canonical_volume_observations": [NUM("volume_quantity"),STR("volume_unit_code",32),sa.Column("volume_scale",sa.SmallInteger),NUM("turnover_amount"),STR("turnover_currency_code",3),sa.Column("turnover_scale",sa.SmallInteger),STR("aggregation_code",32,nullable=False),JSON("volume_context")],
      "canonical_quote_observations": [NUM("bid_price"),NUM("ask_price"),STR("quote_currency_code",3,nullable=False),sa.Column("price_scale",sa.SmallInteger,nullable=False),NUM("bid_size"),NUM("ask_size"),STR("size_unit_code",32),sa.Column("size_scale",sa.SmallInteger),STR("adjustment_state",16,nullable=False,server_default="UNKNOWN"),JSON("quote_context")],
      "canonical_trading_status_observations": [STR("status_code",32,nullable=False),STR("status_reason",256),STR("session_code",32,nullable=False),STR("calendar_code",64,nullable=False),STR("status_catalogue_version",64,nullable=False),JSON("status_context")],
    }
    for table, columns in detail.items():
        op.create_table(table, UUID("canonical_observation_id",primary_key=True), *columns, sa.ForeignKeyConstraint(["canonical_observation_id"],["topicpilot.canonical_observations.id"],ondelete="CASCADE"), schema="topicpilot")
    for table, cols, name in [("canonical_observations",["instrument_id","observed_at","family_code","id"],"ix_canonical_observations_replay"),("canonical_observations",["timeline_entry_id","family_code"],"ix_canonical_observations_timeline_family"),("canonical_observations",["source_id","observed_at"],"ix_canonical_observations_source_time"),("canonical_observations",["quality_state","observed_at"],"ix_canonical_observations_quality_time"),("canonical_observations",["supersedes_id"],"ix_canonical_observations_supersedes")]: op.create_index(name,table,cols,schema="topicpilot")
    checks = [("canonical_price_observations","ck_canonical_price_scale","price_scale BETWEEN 0 AND 18"),("canonical_price_observations","ck_canonical_price_currency_code","price_currency_code ~ '^[A-Z]{3}$'"),("canonical_volume_observations","ck_canonical_volume_scale","volume_scale BETWEEN 0 AND 18 OR volume_scale IS NULL"),("canonical_volume_observations","ck_canonical_turnover_scale","turnover_scale BETWEEN 0 AND 18 OR turnover_scale IS NULL"),("canonical_volume_observations","ck_canonical_volume_quantity_pair","volume_quantity IS NULL OR (volume_unit_code IS NOT NULL AND volume_scale IS NOT NULL)"),("canonical_volume_observations","ck_canonical_turnover_pair","turnover_amount IS NULL OR (turnover_currency_code IS NOT NULL AND turnover_scale IS NOT NULL)"),("canonical_volume_observations","ck_canonical_turnover_currency_code","turnover_currency_code IS NULL OR turnover_currency_code ~ '^[A-Z]{3}$'"),("canonical_quote_observations","ck_canonical_quote_price_scale","price_scale BETWEEN 0 AND 18"),("canonical_quote_observations","ck_canonical_quote_currency_code","quote_currency_code ~ '^[A-Z]{3}$'"),("canonical_quote_observations","ck_canonical_quote_size_scale","size_scale BETWEEN 0 AND 18 OR size_scale IS NULL"),("canonical_quote_observations","ck_canonical_quote_size_pair","(bid_size IS NULL AND ask_size IS NULL) OR (size_unit_code IS NOT NULL AND size_scale IS NOT NULL)")]
    for table, name, expr in checks: op.create_check_constraint(name,table,expr,schema="topicpilot")
    op.execute("""
    CREATE FUNCTION topicpilot.reject_canonical_mutation() RETURNS trigger
    LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'canonical observations are append-only'; END; $$;
    """)
    for table in ["canonical_observations", *detail]:
        op.execute(f"""
        CREATE TRIGGER trg_{table}_append_only
        BEFORE UPDATE OR DELETE ON topicpilot.{table}
        FOR EACH ROW EXECUTE FUNCTION topicpilot.reject_canonical_mutation();
        """)

def downgrade():
    for table in ["canonical_observations", "canonical_price_observations", "canonical_volume_observations", "canonical_quote_observations", "canonical_trading_status_observations"]:
        op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_append_only ON topicpilot.{table}")
    op.execute("DROP FUNCTION IF EXISTS topicpilot.reject_canonical_mutation()")
    for name in ["ix_canonical_observations_supersedes","ix_canonical_observations_quality_time","ix_canonical_observations_source_time","ix_canonical_observations_timeline_family","ix_canonical_observations_replay"]: op.drop_index(name,table_name="canonical_observations",schema="topicpilot")
    for table in ["canonical_trading_status_observations","canonical_quote_observations","canonical_volume_observations","canonical_price_observations","canonical_observations"]: op.drop_table(table,schema="topicpilot")
