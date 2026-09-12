from datetime import date, timedelta

from topicpilot_api.research.ws3_core_v0_validation_failure_mode import (
    BREAKOUT_REJECTION_FAILED_BREAKOUT,
    DATASET_AUTHORITY,
    NO_BREAKOUT_CONTINUED_CONSOLIDATION,
    STRUCTURE_LOSS_BEFORE_BREAKOUT,
    _hypothesis_assessment,
    _path_features,
)


def _path_data(future_closes: list[float], future_highs: list[float]) -> tuple[dict, dict]:
    start = date(2026, 7, 1)
    dates = [start + timedelta(days=index) for index in range(60 + len(future_closes))]
    items = [{"close": 100.0, "high": 100.0, "low": 99.0} for _ in range(60)]
    items.extend(
        {"close": close, "high": high, "low": min(close, 99.0)}
        for close, high in zip(future_closes, future_highs, strict=True)
    )
    instrument_data = {"i1": {"items": items, "dates": dates}}
    row = {
        "instrument_id": "i1",
        "close": 100.0,
        "index": 59,
        "candidate_inputs": {"reference_value": 110.0},
    }
    return row, instrument_data


def test_nontransition_taxonomy_uses_frozen_reference_and_ma60_structurally():
    rejected_row, rejected_data = _path_data(
        [105.0, 95.0] + [100.0] * 8, [115.0, 100.0] + [100.0] * 8
    )
    consolidation_row, consolidation_data = _path_data([102.0] * 10, [105.0] * 10)
    weakened_row, weakened_data = _path_data([95.0] + [95.0] * 9, [105.0] * 10)

    assert (
        _path_features(rejected_row, rejected_data, None)["taxonomy"]
        == BREAKOUT_REJECTION_FAILED_BREAKOUT
    )
    assert (
        _path_features(consolidation_row, consolidation_data, None)["taxonomy"]
        == NO_BREAKOUT_CONTINUED_CONSOLIDATION
    )
    assert (
        _path_features(weakened_row, weakened_data, None)["taxonomy"]
        == STRUCTURE_LOSS_BEFORE_BREAKOUT
    )


def test_hypothesis_assessment_is_bounded_and_does_not_create_ex_ante_rule():
    taxonomy = [
        {"taxonomy": BREAKOUT_REJECTION_FAILED_BREAKOUT},
        {"taxonomy": NO_BREAKOUT_CONTINUED_CONSOLIDATION},
        {"taxonomy": STRUCTURE_LOSS_BEFORE_BREAKOUT},
        {"taxonomy": "UNCLASSIFIED"},
    ]
    path_summary = {
        "A1_LATER_REACHES_A2": {"T5_mean": 0.04},
        "A1_NO_LATER_A2_IN_WINDOW": {"T5_mean": -0.01},
    }
    result = _hypothesis_assessment(
        taxonomy,
        path_summary,
        {"validation_core_T5_mean": -0.04, "validation_nontransition_T5_mean": -0.01},
    )

    assert result["Q5_A1_NOT_TO_A2_approximates_FALSE_BREAKOUT"] == "PARTIALLY"
    assert (
        result["Q6_separation_associated_with_observable_post_formation_failure"] == "YES_BOUNDED"
    )
    assert result["Q7_explains_part_of_negative_validation"] == "YES"
    assert result["Q8_future_ex_ante_discrimination_research"] == "YES_RESEARCH_CANDIDATE"
    assert result["interpretation_guardrail"].endswith("ex-post diagnostics only")


def test_provenance_authority_is_explicit():
    assert "read_historical_bars" in DATASET_AUTHORITY
