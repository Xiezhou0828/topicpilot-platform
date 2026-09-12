from datetime import date

from topicpilot_api.research.ws3_core_v0_baseline_attribution import (
    _core_attribution,
    _persistence,
    _state_value_beyond_ma60,
)


def _metric(mean_return: float, median_return: float, win_rate: float) -> dict:
    return {
        "EVALUABLE_N": 100,
        "mean_return": mean_return,
        "median_return": median_return,
        "win_rate": win_rate,
    }


def test_state_value_requires_frozen_comparison_dimensions():
    state = {str(h): _metric(0.02, 0.01, 0.55) for h in (1, 3, 5, 10)}
    method = {str(h): _metric(0.01, 0.00, 0.50) for h in (1, 3, 5, 10)}
    value, detail = _state_value_beyond_ma60(state, method)
    assert value == "POSITIVE"
    assert detail["positive_horizons"] == 4


def test_persistence_is_descriptive_and_uses_prior_canonical_session():
    rows = [
        {"instrument_id": "i1", "signal_date": date(2026, 7, 1)},
        {"instrument_id": "i1", "signal_date": date(2026, 7, 2)},
        {"instrument_id": "i1", "signal_date": date(2026, 7, 4)},
    ]
    instrument_data = {"i1": {"dates": [date(2026, 7, 1), date(2026, 7, 2), date(2026, 7, 3), date(2026, 7, 4)]}}
    result = _persistence(rows, instrument_data)
    assert result["raw_signal_observations"] == 3
    assert result["repeated_consecutive_observations"] == 1
    assert result["consecutive_persistence_rate"] == 1 / 3
    assert result["max_persistence_days"] == 2
    assert result["episode_trade_performance"] == "NOT_FORMALLY_DEFINED"


def test_core_attribution_marks_high_concentration_as_outlier_driven():
    assert _core_attribution("POSITIVE", "POSITIVE", "HIGH", "LOW") == "OUTLIER_DRIVEN"
