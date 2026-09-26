from __future__ import annotations

import importlib.util
from argparse import Namespace
from pathlib import Path

import pytest

from topicpilot_api.database_maintenance_sources import (
    CANONICAL_MIGRATION_HEAD,
    migration_number,
    migration_schema_status,
)


def _exporter_module():
    path = (
        Path(__file__).parents[3]
        / "scripts"
        / "admin"
        / "export_database_maintenance_workbook.py"
    )
    spec = importlib.util.spec_from_file_location("topicpilot_exporter_under_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_migration_head_comparison_is_explicit() -> None:
    assert migration_schema_status(CANONICAL_MIGRATION_HEAD) == "CURRENT"
    assert (
        migration_schema_status("0036_task_ws4_active_reference_daily_projection")
        == "OLDER_THAN_CANONICAL"
    )
    assert migration_schema_status("0047_future") == "NEWER_THAN_CANONICAL"
    assert migration_schema_status(None) == "UNKNOWN"


def test_migration_number_rejects_unversioned_marker() -> None:
    assert migration_number(CANONICAL_MIGRATION_HEAD) == 46
    assert migration_number("not-a-migration") is None


def test_production_source_does_not_fall_back_to_generic_database_url(monkeypatch) -> None:
    exporter = _exporter_module()
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://legacy.example/topicpilot")
    monkeypatch.delenv("TOPICPILOT_PRODUCTION_DATABASE_URL", raising=False)
    monkeypatch.delenv("TOPICPILOT_PRODUCTION_ADMIN_API_URL", raising=False)
    args = Namespace(
        source="production",
        database_url=None,
        api_url=None,
    )
    with pytest.raises(SystemExit, match="SOURCE_UNAVAILABLE=production"):
        exporter._source_snapshot(args)


def test_legacy_source_has_explicit_default_and_label() -> None:
    exporter = _exporter_module()
    assert "127.0.0.1:5432/topicpilot" in exporter._source_database_url("legacy-local", None)
    assert exporter._unavailable("test")["source_schema_status"] == "UNKNOWN"
