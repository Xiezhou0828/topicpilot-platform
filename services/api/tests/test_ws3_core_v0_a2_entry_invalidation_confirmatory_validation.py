import pytest

from topicpilot_api.research.ws3_core_v0_a2_entry_invalidation_confirmatory_validation import (
    COMBINATION_CANDIDATES,
    DEPTH_CANDIDATE_BANDS,
    ENTRY_CANDIDATE_BANDS,
    FROZEN_SPEC_HASH,
    PATH_STATES,
    RECLAIM_STATES,
    TIME_STATES,
    _aggregate_hash,
    _entry_classification,
    _entry_freeze,
    _event_band,
    _invalidation_freeze,
    _post_loss_row,
    _time_state,
    _wilson,
)


def _authority_stub():
    return {
        "source_canonical_head": "23ff948615f0da6a6242858634d9bacc89b59f2a",
        "frozen_spec_hash": FROZEN_SPEC_HASH,
        "a1_status": "FROZEN_AWAITING_FORWARD_EVIDENCE",
        "a1_candidate_count": 7,
        "source_artifact_hashes": {"upstream.json": "a" * 64},
        "event_definition": {
            "entry_extension": {
                "bands": [
                    {"band": "LE_0PCT", "lower_exclusive": None, "upper_inclusive": 0.0},
                    {"band": "GT_0_TO_1PCT", "lower_exclusive": 0.0, "upper_inclusive": 0.01},
                    {"band": "GT_1_TO_2PCT", "lower_exclusive": 0.01, "upper_inclusive": 0.02},
                    {"band": "GT_2_TO_3PCT", "lower_exclusive": 0.02, "upper_inclusive": 0.03},
                    {"band": "GT_3_TO_5PCT", "lower_exclusive": 0.03, "upper_inclusive": 0.05},
                    {"band": "GT_5PCT", "lower_exclusive": 0.05, "upper_inclusive": None},
                ]
            },
            "reference_loss_reclaim": {
                "depth_bands": [
                    {"band": "NO_LOSS", "lower_exclusive": None, "upper_inclusive": 0.0},
                    {"band": "0_TO_MINUS_1PCT", "lower_exclusive": -0.01, "upper_inclusive": 0.0},
                    {"band": "MINUS_1_TO_2PCT", "lower_exclusive": -0.02, "upper_inclusive": -0.01},
                    {"band": "MINUS_2_TO_3PCT", "lower_exclusive": -0.03, "upper_inclusive": -0.02},
                    {"band": "MINUS_3_TO_5PCT", "lower_exclusive": -0.05, "upper_inclusive": -0.03},
                    {"band": "BELOW_MINUS_5PCT", "lower_exclusive": None, "upper_inclusive": -0.05},
                ]
            },
        },
    }


def test_entry_bands_use_only_frozen_coarse_boundaries():
    assert _event_band(0.0) == "LE_0PCT"
    assert _event_band(0.01) == "GT_0_TO_1PCT"
    assert _event_band(0.02) == "GT_1_TO_2PCT"
    assert _event_band(0.03) == "GT_2_TO_3PCT"
    assert _event_band(0.05) == "GT_3_TO_5PCT"
    assert _event_band(0.050001) == "GT_5PCT"


def test_entry_freeze_has_five_primary_regions_and_no_new_proxy():
    freeze = _entry_freeze(_authority_stub())
    assert freeze["candidate_count"] == 5
    assert [item["extension_band"] for item in freeze["candidate_regions"]] == list(
        ENTRY_CANDIDATE_BANDS
    )
    assert freeze["authorized_entry_proxies"] == [
        "THEORETICAL_REFERENCE_FILL",
        "OBSERVABLE_A2_CLOSE",
        "NEXT_SESSION_OPEN",
        "NEXT_SESSION_CLOSE",
    ]
    assert freeze["frozen_before_confirmatory_outcome_review"] is True
    assert freeze["decision_framework"]["no_entry_threshold_optimization"] is True


def test_invalidation_freeze_has_depth_time_reclaim_path_and_three_combinations():
    freeze = _invalidation_freeze(_authority_stub(), ["REMAINS_ABOVE_REFERENCE", *PATH_STATES])
    assert freeze["candidate_count"] == 15
    assert len(
        [item for item in freeze["candidate_families"] if item["family"] == "REFERENCE_LOSS_DEPTH"]
    ) == len(DEPTH_CANDIDATE_BANDS)
    assert set(freeze["authorized_time_states"][i]["state"] for i in range(3)) == set(TIME_STATES)
    assert set(freeze["authorized_reclaim_states"]) == set(RECLAIM_STATES)
    assert freeze["combination_candidate_ids"] == list(COMBINATION_CANDIDATES)
    assert freeze["maximum_predeclared_combinations"] == 3
    assert freeze["decision_framework"]["no_stop_optimization"] is True


def test_time_state_is_coarse_and_not_dense_search():
    base = {
        "reference_loss": True,
        "sessions_to_reclaim": 1,
        "path_observed_sessions": 10,
        "first_reference_loss_session": 1,
    }
    assert _time_state(base) == "RECLAIM_WITHIN_1_SESSION"
    assert _time_state({**base, "sessions_to_reclaim": 2}) == "RECLAIM_2_SESSIONS"
    assert (
        _time_state({**base, "sessions_to_reclaim": None, "first_reference_loss_session": 1})
        == "RECLAIM_3_PLUS_OR_NO_RECLAIM_H10"
    )


def test_post_loss_metrics_start_strictly_after_loss_session():
    event = {
        "event_id": "e1",
        "market": "TPE",
        "segment": "VALIDATION",
        "path_matured_h10": True,
        "reference_loss": True,
        "first_reference_loss_session": 1,
        "index": 0,
        "reference": 100.0,
        "a2_close": 110.0,
        "_items": [
            {"close": 110, "high": 112, "low": 109},
            {"close": 95, "high": 101, "low": 90},  # first loss; excluded from post-loss H1
            {"close": 102, "high": 105, "low": 98},
            {"close": 108, "high": 109, "low": 100},
        ],
    }
    row = _post_loss_row(event, 1)
    assert row["status"] == "AVAILABLE"
    assert row["post_loss_return_vs_reference"] == pytest.approx(0.02)
    assert row["post_loss_mfe_vs_reference"] == pytest.approx(0.05)
    assert row["post_loss_mae_vs_reference"] == pytest.approx(-0.02)


def test_entry_classification_requires_bounded_multi_metric_evidence():
    candidate = {"candidate_id": "A2_CLOSE_GT_2_TO_3PCT"}
    row = {
        "candidate_id": candidate["candidate_id"],
        "candidate_event_count": 40,
        "entry_available_count": 40,
        "horizon": 5,
        "forward_median": 0.02,
        "forward_win_rate": 0.55,
        "outlier_driven": False,
    }
    row10 = {**row, "horizon": 10, "forward_median": 0.03}
    market = [{**row, "segment_value": "TPE"}, {**row, "segment_value": "TWO"}]
    temporal = [
        {**row, "segment_value": "DEVELOPMENT_AVAILABLE"},
        {**row, "segment_value": "VALIDATION"},
        {**row, "segment_value": "HOLDOUT"},
    ]
    assert _entry_classification(candidate, [row, row10], market, temporal)[0] == "CONFIRMED"
    assert (
        _entry_classification(
            candidate, [{**row, "forward_median": -0.01}, row10], market, temporal
        )[0]
        == "INCONCLUSIVE"
    )


def test_wilson_and_aggregate_hash_are_deterministic():
    low, high = _wilson(8, 10)
    assert 0 < low < high < 1
    assert _aggregate_hash({"b": "b" * 64, "a": "a" * 64}) == _aggregate_hash(
        {"a": "a" * 64, "b": "b" * 64}
    )
