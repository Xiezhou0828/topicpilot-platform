from __future__ import annotations

import hashlib
from pathlib import Path

from topicpilot_api.research.decision_intelligence import (
    HORIZONS,
    OUTPUT_FILES,
    build_dataset,
    run_c1,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_c1_dataset_is_bounded_and_explicitly_missing() -> None:
    dataset = build_dataset(_repo_root())

    assert len(dataset.feature_vectors) > 0
    assert len(dataset.outcome_labels) == len(dataset.feature_vectors) * len(HORIZONS)
    assert all(vector.as_of.isoformat() >= "2026-02-03" for vector in dataset.feature_vectors)
    assert all(vector.as_of.isoformat() <= "2026-08-13" for vector in dataset.feature_vectors)
    assert all(vector.grade is None for vector in dataset.feature_vectors)
    assert all(label.market_relative_return is None for label in dataset.outcome_labels)
    label_keys = {
        (label.event_id, label.topic_id, label.horizon) for label in dataset.outcome_labels
    }
    assert len(label_keys) == len(dataset.outcome_labels)
    for label in dataset.outcome_labels:
        if label.status == "AVAILABLE":
            assert label.target_date is not None
            assert label.target_date > label.signal_date


def test_c1_replay_is_byte_deterministic(tmp_path: Path) -> None:
    root = _repo_root()
    first = tmp_path / "first"
    second = tmp_path / "second"

    run_c1(first, source_root=root)
    run_c1(second, source_root=root)

    for name in OUTPUT_FILES:
        assert (first / name).read_bytes() == (second / name).read_bytes(), name
        assert _sha256(first / name) == _sha256(second / name), name


def test_c1_unavailable_dimensions_fail_closed(tmp_path: Path) -> None:
    result = run_c1(tmp_path / "output", source_root=_repo_root())

    assert {row["status"] for row in result.grade_lifecycle} == {"INSUFFICIENT_HISTORICAL_GRADE"}
    assert {row["status"] for row in result.market_regime} == {"INSUFFICIENT_MARKET_REGIME_HISTORY"}
    assert result.manifest["canonical_adoption"] == "NOT_CANONICAL_UNTIL_MAIN_INTEGRATION"
    assert result.manifest["contracts"]["production_mutation"] is False
    assert result.manifest["contracts"]["migration"] is False
