from __future__ import annotations

import json
from pathlib import Path

import pytest

from topicpilot_api.reference_data import (
    BundleValidationError,
    build_bundle_from_sources,
    load_bundle,
)

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "src" / "topicpilot_api" / "reference_data" / "bundles" / "tw-reference-v1"


def test_committed_tw_reference_bundle_is_derived_and_contains_known_evidence():
    bundle = load_bundle(BUNDLE)
    assert bundle.manifest["generatedOrCurated"] == "GENERATED_WITH_CURATED_GOVERNANCE_INPUTS"
    assert bundle.summary() == {
        "marketCount": 2,
        "instrumentCount": 507,
        "instrumentCountByMarket": {"TPE": 314, "TWO": 193},
        "currencyCount": 1,
        "timezoneCount": 1,
        "sessionCount": 1,
        "tradingStatusCount": 8,
        "adjustmentCount": 3,
        "calendarDateCount": 24,
        "calendarHolidayCount": 23,
        "calendarSuspendedCount": 1,
        "lifecycleEventCount": 4,
    }
    assert bundle.evidence["suspensions"]["6806"]["status"] == "DELISTED"
    assert bundle.evidence["suspensions"]["6806"]["evidenceId"] == "TWSE-DELISTED-6806-20260623"
    assert bundle.evidence["suspensions"]["1563"]["events"][0]["status"] == "SUSPENDED"
    assert bundle.evidence["suspensions"]["1563"]["events"][0]["sourceDocument"].startswith("1563 巧新")
    by_identity = {
        (row["market_code"], row["instrument_code"], row["status_code"]): row
        for row in bundle.instrument_lifecycles
    }
    assert by_identity[("TPE", "6806", "DELISTED")]["effective_from"] == "2026-06-23"
    assert by_identity[("TPE", "1563", "SUSPENDED")]["effective_from"] == "2026-08-27"
    assert by_identity[("TPE", "1563", "SUSPENDED")]["effective_to"] == "2026-09-04"
    assert by_identity[("TWO", "5371", "SUSPENDED")]["effective_from"] == "2026-08-24"
    assert by_identity[("TWO", "5371", "SUSPENDED")]["effective_to"] == "2026-09-02"
    assert by_identity[("TWO", "5371", "TERMINATED")]["effective_from"] == "2026-09-03"


def test_bundle_generation_derives_instruments_without_a_count_business_rule(tmp_path: Path):
    stock = tmp_path / "stock.tsv"
    stock.write_text(
        "股號\t名稱\t市場代碼\n2330\tTSMC\tTPE\n6488\tTest\tTWO\n\tIncomplete\tTPE\n",
        encoding="utf-8",
    )
    calendar = tmp_path / "calendar.json"
    calendar.write_text(
        json.dumps(
            {
                "market": "TWSE",
                "timezone": "Asia/Taipei",
                "version": "test-calendar",
                "source": "test authority",
                "holidays": {"2026-01-01": "holiday"},
                "suspended": {"2026-01-02": "suspended"},
            }
        ),
        encoding="utf-8",
    )
    evidence = tmp_path / "evidence.json"
    evidence.write_text(json.dumps({"version": 1, "suspensions": {}}), encoding="utf-8")
    adjustments = tmp_path / "adjustments.json"
    adjustments.write_text(json.dumps({"codes": ["UNKNOWN"]}), encoding="utf-8")

    bundle = build_bundle_from_sources(
        stock_source=stock,
        calendar_source=calendar,
        evidence_source=evidence,
        adjustment_source=adjustments,
        version="test-reference-v1",
    )
    assert bundle.summary()["instrumentCount"] == 2
    assert bundle.manifest["sourceArtifacts"][0]["inputRowCount"] == 3
    assert bundle.manifest["sourceArtifacts"][0]["skippedRowCount"] == 1


def test_bundle_rejects_duplicate_calendar_dates(tmp_path: Path):
    stock = tmp_path / "stock.tsv"
    stock.write_text("股號\t名稱\t市場代碼\n2330\tTSMC\tTPE\n", encoding="utf-8")
    calendar = tmp_path / "calendar.json"
    calendar.write_text(
        json.dumps(
            {
                "timezone": "Asia/Taipei",
                "version": "test",
                "source": "test",
                "holidays": {"2026-01-01": "holiday"},
                "suspended": {"2026-01-01": "suspended"},
            }
        ),
        encoding="utf-8",
    )
    evidence = tmp_path / "evidence.json"
    evidence.write_text(json.dumps({"suspensions": {}}), encoding="utf-8")
    adjustments = tmp_path / "adjustments.json"
    adjustments.write_text(json.dumps({"codes": ["UNKNOWN"]}), encoding="utf-8")

    with pytest.raises(BundleValidationError, match="duplicate calendar date"):
        build_bundle_from_sources(
            stock_source=stock,
            calendar_source=calendar,
            evidence_source=evidence,
            adjustment_source=adjustments,
        )
