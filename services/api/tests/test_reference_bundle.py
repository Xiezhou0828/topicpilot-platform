from __future__ import annotations

import json
from pathlib import Path

import pytest

from topicpilot_api.reference_bundle_cli import main as reference_bundle_main
from topicpilot_api.reference_data import (
    BUNDLE_FILE_NAMES,
    BundleValidationError,
    build_bundle_from_sources,
    load_bundle,
    write_bundle,
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
        "lifecycleEventCount": 5,
    }
    assert bundle.evidence["suspensions"]["6806"]["status"] == "DELISTED"
    assert bundle.evidence["suspensions"]["6806"]["evidenceId"] == "TWSE-DELISTED-6806-20260623"
    assert bundle.evidence["suspensions"]["1563"]["events"][0]["status"] == "SUSPENDED"
    assert bundle.evidence["suspensions"]["6129"]["events"][0]["status"] == "SUSPENDED"
    assert bundle.evidence["suspensions"]["6129"]["events"][0][
        "sourceDocument"
    ].startswith("6129 普誠")
    by_identity = {
        (row["market_code"], row["instrument_code"], row["status_code"]): row
        for row in bundle.instrument_lifecycles
    }
    assert by_identity[("TPE", "6806", "DELISTED")]["effective_from"] == "2026-06-23"
    assert by_identity[("TWO", "5371", "SUSPENDED")]["effective_from"] == "2026-08-24"
    assert by_identity[("TWO", "5371", "SUSPENDED")]["effective_to"] == "2026-09-02"
    assert by_identity[("TWO", "5371", "TERMINATED")]["effective_from"] == "2026-09-03"
    assert by_identity[("TPE", "1563", "SUSPENDED")]["effective_from"] == "2026-08-27"
    assert by_identity[("TPE", "1563", "SUSPENDED")]["effective_to"] == "2026-09-04"
    assert by_identity[("TWO", "6129", "SUSPENDED")]["effective_from"] == "2026-09-03"
    assert by_identity[("TWO", "6129", "SUSPENDED")]["effective_to"] == "2026-09-11"


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


def _generation_sources(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    stock = tmp_path / "stock.tsv"
    stock.write_text(
        "股號\t名稱\t市場代碼\n2330\tTSMC\tTPE\n6488\tTest\tTWO\n",
        encoding="utf-8",
    )
    calendar = tmp_path / "calendar.json"
    calendar.write_text(
        json.dumps(
            {
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
    return stock, calendar, evidence, adjustments


def test_same_generation_inputs_produce_byte_identical_bundles(tmp_path: Path):
    stock, calendar, evidence, adjustments = _generation_sources(tmp_path)
    first = build_bundle_from_sources(
        stock_source=stock,
        calendar_source=calendar,
        evidence_source=evidence,
        adjustment_source=adjustments,
        version="test-reference-v1",
    )
    second = build_bundle_from_sources(
        stock_source=stock,
        calendar_source=calendar,
        evidence_source=evidence,
        adjustment_source=adjustments,
        version="test-reference-v1",
    )
    first_dir = write_bundle(first, tmp_path / "first")
    second_dir = write_bundle(second, tmp_path / "second")

    assert [row["code"] for row in first.trading_statuses] == [
        "AVAILABLE",
        "DELISTED",
        "EXCHANGE_CONFIRMED_NO_DATA",
        "NO_TRADE",
        "OPEN",
        "SUSPENDED",
        "UNKNOWN",
        "TERMINATED",
    ]
    for filename in ("manifest.json", *BUNDLE_FILE_NAMES):
        assert (first_dir / filename).read_bytes() == (second_dir / filename).read_bytes()


def test_check_mode_reports_semantic_drift_and_write_mode_repairs_it(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    stock, calendar, evidence, adjustments = _generation_sources(tmp_path)
    canonical = build_bundle_from_sources(
        stock_source=stock,
        calendar_source=calendar,
        evidence_source=evidence,
        adjustment_source=adjustments,
        version="test-reference-v1",
    )
    stale_instrument = {**canonical.instruments[0], "name": "STALE"}
    stale = canonical.__class__(
        manifest=dict(canonical.manifest),
        markets=canonical.markets,
        instruments=(stale_instrument, *canonical.instruments[1:]),
        currencies=canonical.currencies,
        timezones=canonical.timezones,
        sessions=canonical.sessions,
        trading_statuses=canonical.trading_statuses,
        adjustments=canonical.adjustments,
        calendar_dates=canonical.calendar_dates,
        instrument_lifecycles=canonical.instrument_lifecycles,
        evidence=canonical.evidence,
    )
    bundle_dir = write_bundle(stale, tmp_path / "checked")
    check_args = [
        "check",
        "--bundle-dir",
        str(bundle_dir),
        "--stock-source",
        str(stock),
        "--calendar-source",
        str(calendar),
        "--evidence-source",
        str(evidence),
        "--adjustment-source",
        str(adjustments),
    ]

    assert reference_bundle_main(check_args) == 2
    report = json.loads(capsys.readouterr().out)
    assert report["CURRENT_BUNDLE_MATCHES_CANONICAL_GENERATOR"] == "NO"
    assert "instruments.json" in report["changedArtifacts"]
    assert any(
        item["artifactPath"] == "instruments.json"
        and item["semanticPath"] == '$[0]["name"]'
        and item["expected"] == "STALE"
        and item["actual"] == "TSMC"
        for item in report["differences"]
    )

    assert reference_bundle_main(
        [
            "generate",
            "--stock-source",
            str(stock),
            "--calendar-source",
            str(calendar),
            "--evidence-source",
            str(evidence),
            "--adjustment-source",
            str(adjustments),
            "--reference-version",
            "test-reference-v1",
            "--output-dir",
            str(bundle_dir),
        ]
    ) == 0
    capsys.readouterr()
    assert reference_bundle_main(check_args) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["CURRENT_BUNDLE_MATCHES_CANONICAL_GENERATOR"] == "YES"


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
