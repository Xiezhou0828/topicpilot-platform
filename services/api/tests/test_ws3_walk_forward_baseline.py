from datetime import date
from decimal import Decimal

from topicpilot_api.research.ws3_walk_forward_baseline import (
    _edge,
    _forward_event_excluded,
    _metric,
    _sma,
)


def test_sma_requires_full_warmup_window():
    assert _sma([Decimal("1")] * 59, period=60) is None
    assert _sma([Decimal("1")] * 60, period=60) == Decimal("1")


def test_forward_event_exclusion_is_strictly_after_signal_date():
    assert not _forward_event_excluded(
        [{"primary_effective_date": "2026-07-01"}],
        date(2026, 7, 1),
        date(2026, 7, 2),
    )
    assert _forward_event_excluded(
        [{"primary_effective_date": "2026-07-02"}],
        date(2026, 7, 1),
        date(2026, 7, 3),
    )


def test_metric_censors_missing_targets_without_zero_filling():
    observations = [
        {"returns": {1: 0.10}, "event_excluded_horizons": set()},
        {"returns": {}, "event_excluded_horizons": set()},
        {
            "returns": {},
            "event_excluded_horizons": {1},
        },
    ]
    result = _metric(observations, horizon=1)
    assert result["N"] == 3
    assert result["EVALUABLE_N"] == 1
    assert result["CENSORED_N"] == 1
    assert result["EVENT_EXCLUDED_N"] == 1
    assert result["mean_return"] == 0.10


def test_edge_requires_all_frozen_comparison_dimensions():
    candidate = [
        {"returns": {1: 0.02, 3: 0.02, 5: 0.02, 10: 0.02}, "event_excluded_horizons": set()},
        {"returns": {1: 0.03, 3: 0.03, 5: 0.03, 10: 0.03}, "event_excluded_horizons": set()},
    ]
    baseline = [
        {"returns": {1: 0.01, 3: 0.01, 5: 0.01, 10: 0.01}, "event_excluded_horizons": set()},
        {"returns": {1: 0.02, 3: 0.02, 5: 0.02, 10: 0.02}, "event_excluded_horizons": set()},
    ]
    assert _edge(candidate, baseline) == "POSITIVE"
