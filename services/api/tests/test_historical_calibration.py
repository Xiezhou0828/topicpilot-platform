from datetime import date

from topicpilot_api.topic_engine.historical_calibration import (
    ABSOLUTE,
    RELATIVE,
    CalibrationRow,
    assess_row,
    calibration_audit,
    candidate_parameter_bundle,
    member_return_distributions,
    topic_role_day_aggregates,
)


def _row(**overrides) -> CalibrationRow:
    data = {
        "trading_date": date(2026, 8, 7),
        "topic_id": "topic-1",
        "instrument_id": "instrument-1",
        "market": "TPE",
        "structural_role": "CORE",
        "absolute_return": 2.0,
        "benchmark_identity": "TAIEX",
        "benchmark_return": 1.0,
        "relative_return": 1.0,
        "role_authority_status": "PIT_APPROVED",
        "role_authority_version": "roles.v1",
        "role_effective_from": date(2026, 8, 1),
        "role_effective_to": None,
        "membership_status": "FORMAL_ACTIVE",
        "score_importance": 1.0,
        "score_importance_version": "importance.v1",
        "source_kind": "CANONICAL_HISTORICAL",
        "data_freshness": "AS_OF_TRADING_DATE",
        "coverage_status": "COMPLETE",
        "formal_member_count": 3,
    }
    data.update(overrides)
    return CalibrationRow(**data)


def test_point_in_time_row_accepts_own_market_benchmark_alias():
    decision = assess_row(_row())

    assert decision.absolute is True
    assert decision.relative is True
    assert decision.weighted is True


def test_relative_row_rejects_wrong_benchmark_without_rejecting_absolute_row():
    decision = assess_row(_row(benchmark_identity="TPEX_INDEX"))

    assert decision.absolute is True
    assert decision.relative is False
    assert "BENCHMARK_IDENTITY_MISMATCH" in decision.reasons


def test_current_taxonomy_or_missing_authority_is_not_calibration_truth():
    decision = assess_row(
        _row(
            source_kind="CURRENT_TAXONOMY_HISTORICAL_RECONSTRUCTION",
            role_authority_status="UNKNOWN",
        )
    )

    assert decision.absolute is False
    assert "ROLE_AUTHORITY_NOT_PIT_APPROVED" in decision.reasons
    assert "SOURCE_NOT_CANONICAL_HISTORICAL" in decision.reasons


def test_descriptive_distributions_and_role_day_aggregates_are_deterministic():
    rows = (_row(), _row(instrument_id="instrument-2", absolute_return=4.0, relative_return=3.0))
    distribution = member_return_distributions(rows, view=ABSOLUTE)
    aggregate = topic_role_day_aggregates(rows, view=RELATIVE)

    assert distribution["eligibleMemberRows"] == 2
    assert distribution["groups"]["TWSE:CORE"]["percentiles"]["p50"] == 3.0
    assert aggregate["aggregateCount"] == 1
    assert aggregate["aggregates"][0]["positiveBreadth"] == 1.0
    assert aggregate["aggregates"][0]["strongBreadth"] is None


def test_empty_input_keeps_all_candidate_values_unresolved_and_inactive():
    audit = calibration_audit(())
    bundle = candidate_parameter_bundle(audit)

    assert audit["status"] == "INSUFFICIENT_DATA"
    assert bundle["status"] == "INSUFFICIENT_DATA"
    assert all(parameter["candidateValue"] is None for parameter in bundle["parameters"])
    assert all(parameter["productionActive"] is False for parameter in bundle["parameters"])
