from __future__ import annotations

import math
from decimal import Decimal
from fractions import Fraction

import pytest

from topicpilot_api.live.checkpoint_contract import (
    canonical_checkpoint_json,
    canonicalize_checkpoint_payload,
    checkpoint_stable_hash,
)


@pytest.mark.parametrize("value", [30, 30.0, Decimal("30.0"), Decimal("30.000")])
def test_checkpoint_numeric_equivalence_is_explicit(value):
    assert checkpoint_stable_hash({"backoffSeconds": value}) == checkpoint_stable_hash(
        {"backoffSeconds": 30}
    )


def test_checkpoint_numeric_and_string_types_remain_distinct():
    assert checkpoint_stable_hash({"value": 30}) != checkpoint_stable_hash({"value": "30"})
    assert canonicalize_checkpoint_payload({"value": "30"}) == {"value": "30"}


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf, Decimal("NaN")])
def test_checkpoint_non_finite_numbers_fail_closed(value):
    with pytest.raises(ValueError, match="finite numeric"):
        canonical_checkpoint_json({"value": value})


def test_checkpoint_unknown_numeric_type_fails_closed():
    with pytest.raises(TypeError, match="unsupported checkpoint canonical value"):
        canonical_checkpoint_json({"value": Fraction(1, 2)})


def test_checkpoint_hash_is_ordered_null_preserving_and_deterministic():
    first = {"z": None, "nested": {"b": 2, "a": 1}, "items": [1, 2]}
    second = {"items": [1, 2], "nested": {"a": 1, "b": 2}, "z": None}

    assert canonical_checkpoint_json(first) == canonical_checkpoint_json(second)
    assert checkpoint_stable_hash(first) == checkpoint_stable_hash(second)
    assert checkpoint_stable_hash(first) != checkpoint_stable_hash(
        {**first, "items": [1, 3]}
    )


def test_checkpoint_hash_regression_for_status_resolution_payload():
    payload = {
        "runId": "run-1",
        "batchKey": "STATUS_RESOLUTION",
        "batchNumber": 120,
        "attemptNumber": 1,
        "status": "IN_PROGRESS",
        "processedCount": 0,
        "succeededCount": 0,
        "failedCount": 0,
        "skippedCount": 0,
        "retryCount": 0,
        "providerRequestCount": None,
        "providerFailureCount": None,
        "metadata": {
            "backoffSeconds": 30.0,
            "checkpointSemantic": "TRADING_STATUS_AUTHORITY_RESOLUTION",
            "providerMetricsApplicability": "NOT_APPLICABLE",
        },
    }

    assert checkpoint_stable_hash(payload) == (
        "6fb8366ed70fa3d10d0808ce9b3c68e9617afcd8a890dcc68338af13e6c0b6ce"
    )
