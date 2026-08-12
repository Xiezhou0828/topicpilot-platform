from __future__ import annotations

import json
from pathlib import Path

from topicpilot_api.detectors import (
    RANGE_DETECTOR_ID,
    RANGE_DETECTOR_VERSION,
    DetectorConfig,
    DetectorContext,
    DetectorRegistry,
    DetectorRunner,
    Generation,
    Lineage,
    Result,
    Status,
    register_range_detector,
)

FIXTURES = Path(__file__).parent / "fixtures" / "range"


def make_context(payload):
    return DetectorContext(
        "inv",
        "run",
        "corr",
        Generation.NEXT_V2,
        RANGE_DETECTOR_ID,
        RANGE_DETECTOR_VERSION,
        "1",
        payload,
        "synthetic",
        "2026-01-30",
        Lineage("synthetic-range", input_hash="hash"),
        timeframe="DAILY",
    )


def run(name, config=None):
    registry = DetectorRegistry()
    register_range_detector(registry)
    ctx = make_context(json.loads((FIXTURES / name).read_text()))
    return DetectorRunner(registry).run(
        ctx, DetectorConfig.resolve(RANGE_DETECTOR_ID, "range-1", config)
    )


def test_range_pass_fixture_has_boundaries_and_is_deterministic():
    a = run("clear_range.json")
    b = run("clear_range.json")
    assert a.result is Result.PASS
    assert a.status is Status.COMPLETED
    assert a.evidence.facts == b.evidence.facts
    assert a.confidence is not None and 0 <= a.confidence <= 1
    assert a.evidence.facts["timeframe"] == "DAILY"
    assert a.evidence.facts["compression_score"] > 0
    assert a.evidence.facts["confidence_method"]


def test_range_fail_fixture():
    result = run("unstable.json")
    assert result.result is Result.FAIL
    assert (
        result.evidence.facts["support_touch_count"] < 2
        or result.evidence.facts["resistance_touch_count"] < 2
    )


def test_confidence_reflects_range_quality():
    clear = run("clear_range.json")
    unstable = run("unstable.json")
    expansion = run("expansion_trend.json")
    assert clear.confidence > unstable.confidence > expansion.confidence
    assert clear.evidence.facts["compression_score"] > expansion.evidence.facts["compression_score"]
    assert clear.evidence.facts["duration_score"] >= unstable.evidence.facts["duration_score"]


def test_range_expansion_trend_does_not_pass_as_stable_range():
    result = run("expansion_trend.json")
    assert result.result is Result.FAIL
    assert result.evidence.facts["directional_expansion_ratio"] > 0.75


def test_range_unknown_for_insufficient_history():
    result = run("insufficient.json")
    assert result.result is Result.UNKNOWN
    assert result.diagnostics.code == "INSUFFICIENT_HISTORY"
    assert result.confidence is None


def test_range_invalid_input():
    result = run("invalid.json")
    assert result.result is Result.UNKNOWN
    assert result.status is Status.INVALID_INPUT
    assert result.diagnostics.code == "INVALID_INPUT"


def test_range_configuration_is_propagated():
    result = run("clear_range.json", {"lookback": 10, "minimum_duration": 10})
    assert result.configuration_version == "range-1"


def test_range_registry_entry_is_explicit():
    registry = DetectorRegistry()
    register_range_detector(registry)
    entry = registry.lookup(RANGE_DETECTOR_ID, RANGE_DETECTOR_VERSION)
    assert entry.detector.detector_id == RANGE_DETECTOR_ID
