from datetime import date
from pathlib import Path

from topicpilot_api.topic_lifecycle_calibration import (
    CALIBRATION_REVIEW_VERSION,
    LifecycleCalibrationRecord,
    build_review_payload,
    export_csv,
    export_json,
    export_markdown,
    records_from_rows,
    select_representative_cases,
    summarize_records,
    validate_pm_result,
)
from topicpilot_api.topic_lifecycle_engine import (
    DECLINING,
    MAIN_RISE,
    MATURE,
    SPROUTING,
)


def _row(
    slug: str,
    day: str,
    *,
    final: str | None,
    previous: str | None = None,
    candidate: str | None = None,
    decision: str = "HOLD_CURRENT_STAGE",
    data_status: str = "SHADOW",
    confidence: float = 0.8,
    sample_small: bool = False,
    leader: str = "inst-1",
):
    return {
        "topic_id": f"id-{slug}",
        "topic_slug": slug,
        "evaluation_date": date.fromisoformat(day),
        "previous_stage": previous,
        "candidate_stage": candidate,
        "final_stage": final,
        "stage_entered_at": date.fromisoformat(day) if final else None,
        "stage_trading_days": 1 if final else None,
        "transition_decision": decision,
        "transition_reason": "fixture-review-only",
        "evaluation_status": "EVALUATED" if final else "INSUFFICIENT_DATA",
        "data_status": data_status,
        "policy_version": "topic-lifecycle-policy.provisional.1",
        "calculation_version": "topic-lifecycle-shadow.v1",
        "average_change": 2.1,
        "coverage_pct": 92.0,
        "leadership_evidence": {
            "leaderSemanticAvailable": False,
            "leaderId": leader,
            "leaderChangePct": 6.8,
        },
        "diffusion_evidence": {
            "expectedMemberCount": 20,
            "observedMemberCount": 18,
            "coveragePct": 92.0,
            "positiveBreadth": 0.78,
        },
        "group_strength_evidence": {
            "averageChangePct": 2.1,
            "strongBreadth": 0.41,
            "weakRatio": 0.05,
        },
        "divergence_decay_evidence": {},
        "persistence_evidence": {
            "previousCandidateStage": candidate,
        },
        "sample_confidence": {
            "confidence": confidence,
            "sampleConfidence": 0.9,
            "smallSample": sample_small,
        },
        "confirmation_state": {
            "candidateStreak": 2,
            "strongSignal": decision == "JUMP_TRANSITION",
        },
    }


def test_review_record_maps_all_pm_contract_groups_and_keeps_pm_fields_blank():
    record = LifecycleCalibrationRecord.from_row(
        _row("alpha", "2026-08-10", final=MAIN_RISE, candidate=MAIN_RISE),
        topic_display_name="Alpha Topic",
    )
    assert record.topic_display_name == "Alpha Topic"
    assert record.positive_breadth == 0.78
    assert record.strong_breadth == 0.41
    assert record.leader_proxy_stock == "inst-1"
    assert record.pm_expected_stage is None
    assert record.pm_result is None
    assert record.pm_note is None


def test_summary_counts_replay_transitions_and_statuses_deterministically():
    records = records_from_rows(
        [
            _row("zeta", "2026-08-11", final=MATURE, previous=MAIN_RISE),
            _row(
                "alpha",
                "2026-08-10",
                final=MAIN_RISE,
                previous=MATURE,
                candidate=MAIN_RISE,
                decision="JUMP_TRANSITION",
            ),
            _row(
                "beta",
                "2026-08-10",
                final=None,
                candidate=SPROUTING,
                data_status="INSUFFICIENT_DATA",
                confidence=0.2,
                sample_small=True,
            ),
            _row(
                "gamma",
                "2026-08-10",
                final=DECLINING,
                candidate=DECLINING,
                decision="JUMP_TRANSITION",
            ),
        ]
    )
    summary = summarize_records(records)
    assert summary["calibrationReviewVersion"] == CALIBRATION_REVIEW_VERSION
    assert summary["tradingDates"] == ["2026-08-10", "2026-08-11"]
    assert summary["topicsEvaluated"] == 4
    assert summary["insufficientDataCount"] == 1
    assert summary["strongJumpCount"] == 1
    assert summary["strongDeclineCount"] == 1
    assert summary["reentryCount"] == 1
    assert summary["stageDistribution"]["PENDING"] == 1


def test_representatives_return_missing_cases_without_inventing_records():
    records = records_from_rows(
        [
            _row("alpha", "2026-08-10", final=SPROUTING),
            _row(
                "beta", "2026-08-10", final=None, data_status="INSUFFICIENT_DATA", sample_small=True
            ),
            _row(
                "confirmed",
                "2026-08-10",
                final=MAIN_RISE,
                previous="FERMENTING",
                candidate=MAIN_RISE,
                decision="CONFIRMED_TRANSITION",
            ),
            _row(
                "jump",
                "2026-08-10",
                final=MAIN_RISE,
                previous=MATURE,
                candidate=MAIN_RISE,
                decision="JUMP_TRANSITION",
            ),
            _row(
                "decline",
                "2026-08-10",
                final=DECLINING,
                previous=MATURE,
                candidate=DECLINING,
                decision="JUMP_TRANSITION",
            ),
            _row(
                "candidate",
                "2026-08-10",
                final=MATURE,
                previous=MAIN_RISE,
                candidate=DECLINING,
                decision="HOLD_CONFIRMATION",
            ),
        ]
    )
    selected = select_representative_cases(records)
    assert selected["stage_sprouting"]["found"] is True
    assert selected["stage_fermenting"]["found"] is False
    assert selected["confirmed_transition"]["found"] is True
    assert selected["strong_jump"]["found"] is True
    assert selected["strong_decline"]["found"] is True
    assert selected["mature_main_rise_reentry"]["found"] is True
    assert selected["transition_candidate"]["found"] is True
    assert selected["insufficient_data"]["found"] is True
    assert selected["small_sample"]["found"] is True


def test_exports_are_deterministic_and_include_pm_review_placeholders():
    records = records_from_rows([_row("alpha", "2026-08-10", final=MAIN_RISE)])
    payload = build_review_payload(records)
    assert export_json(payload) == export_json(build_review_payload(records))
    csv_output = export_csv(records)
    assert "pm_expected_stage" in csv_output
    assert "pm_result" in csv_output
    markdown = export_markdown(payload)
    assert "## Replay Summary" in markdown
    assert "## Representative Cases" in markdown
    assert "PM Expected" in markdown
    assert "| alpha |" in markdown


def test_empty_export_is_data_gated_and_reports_missing_cases():
    payload = build_review_payload([])
    assert payload["summary"]["historicalReplay"] == "BLOCKED_BY_DATA"
    assert payload["summary"]["pmCalibration"] == "WAITING_FOR_DATA"
    assert all(not item["found"] for item in payload["representatives"].values())
    assert "WAITING_FOR_FORMAL_OBSERVATIONS" not in export_csv([])
    assert "BLOCKED_BY_DATA" in export_markdown(payload)


def test_pm_review_result_values_are_explicit_and_not_engine_semantics():
    assert validate_pm_result("MATCH") == "MATCH"
    assert validate_pm_result(None) is None
    try:
        validate_pm_result("MAIN_RISE")
    except ValueError as exc:
        assert "unsupported PM calibration result" in str(exc)
    else:
        raise AssertionError("invalid PM result must be rejected")


def test_calibration_module_has_no_fixture_market_source_dependency():
    module = Path(__file__).parents[1] / "src" / "topicpilot_api" / "topic_lifecycle_calibration.py"
    source = module.read_text(encoding="utf-8").lower()
    assert "fixtures/" not in source
    assert "yahoo" not in source
    assert "google sheets" not in source


def test_export_projection_does_not_mutate_persisted_review_record():
    records = records_from_rows([_row("alpha", "2026-08-10", final=MAIN_RISE)])
    before = records[0]
    payload = build_review_payload(records)
    export_json(payload)
    export_csv(records)
    export_markdown(payload)
    assert records[0] == before
