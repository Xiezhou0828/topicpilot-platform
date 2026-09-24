from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_formal_relation_reader_uses_approved_authority_only():
    source = (ROOT / "src/topicpilot_api/production_read_model.py").read_text(encoding="utf-8")
    assert "relation_weight_authorities" in source
    assert "authority.approval_state = 'APPROVED'" in source
    assert "relationship_metadata ->> 'relationWeight'" not in source
    assert "relationship_metadata ->> 'weight'" not in source


def test_today_and_score_modules_do_not_import_relation_weight_authority():
    for relative in (
        "src/topicpilot_api/topic_daily_state.py",
        "src/topicpilot_api/topic_engine/score_projection.py",
        "src/topicpilot_api/topic_lifecycle_engine.py",
    ):
        source = (ROOT / relative).read_text(encoding="utf-8")
        assert "relation_weight_authority" not in source
