from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import CheckConstraint, UniqueConstraint

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "alembic" / "versions" / "0019_phase3_5_001b_canonical_observations.py"


def test_canonical_revision_is_linear_after_0018():
    source = MIGRATION.read_text(encoding="utf-8")
    assert 'revision = "0019_phase3_5_001b_canonical_observations"' in source
    assert 'down_revision = "0018_phase3_4_006_observation_timeline"' in source
    config = Config(str(ROOT / "alembic.ini"))
    script = ScriptDirectory.from_config(config)
    assert [head.revision for head in script.get_revisions("heads")] == [
        "0024_task_be_007_topic_snapshots"
    ]


def test_migration_contains_only_approved_families_and_no_current_unique_constraint():
    source = MIGRATION.read_text(encoding="utf-8")
    for table in ("canonical_observations", "canonical_price_observations", "canonical_volume_observations", "canonical_quote_observations", "canonical_trading_status_observations"):
        assert table in source
    assert "partial" not in source.lower()
    assert "supersedes_id" in source
    assert "uq_canonical_observations_idempotency" in source


def test_orm_registry_exposes_canonical_models_and_structural_constraints():
    from topicpilot_api.orm.models import CanonicalObservation, CanonicalPriceObservation

    assert CanonicalObservation.__tablename__ == "canonical_observations"
    assert CanonicalPriceObservation.__tablename__ == "canonical_price_observations"
    assert any(isinstance(c, UniqueConstraint) and c.name == "uq_canonical_observations_idempotency" for c in CanonicalObservation.__table__.constraints)
    assert any(isinstance(c, CheckConstraint) and c.name.endswith("ck_canonical_observations_no_self_supersession") for c in CanonicalObservation.__table__.constraints)
