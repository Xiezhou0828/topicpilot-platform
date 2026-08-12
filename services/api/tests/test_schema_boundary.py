from pathlib import Path

API_SRC = Path(__file__).parents[1] / "src" / "topicpilot_api"


def test_compatibility_sql_is_explicitly_owned_by_public_schema() -> None:
    for name in ("repository.py", "snapshot.py"):
        source = (API_SRC / name).read_text(encoding="utf-8")
        assert "FROM public." in source
        assert "JOIN public." in source
        assert "FROM stocks " not in source
        assert "FROM topics " not in source
        assert "FROM strategy_runs " not in source
        assert "FROM topic_snapshots " not in source


def test_v2_orm_has_explicit_topicpilot_schema_boundary() -> None:
    base = (API_SRC / "orm" / "base.py").read_text(encoding="utf-8")
    models = (API_SRC / "orm" / "models.py").read_text(encoding="utf-8")
    assert 'MetaData(schema="topicpilot"' in base
    assert 'ForeignKey("topicpilot.' in models
