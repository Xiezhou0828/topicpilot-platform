from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest

from topicpilot_api.live.post_close import (
    PostClosePreconditionError,
    PostCloseUpdater,
)


def _identity(market: str, code: str, identifier: int):
    return (
        SimpleNamespace(id=identifier, instrument_code=code),
        SimpleNamespace(code=market),
    )


def test_post_close_universe_validation_is_exact_and_duplicate_safe():
    expected = {
        "TPE": ("2330", "2317"),
        "TWO": ("4979",),
    }
    instruments = [
        _identity("TPE", "2317", 1),
        _identity("TPE", "2330", 2),
        _identity("TWO", "4979", 3),
    ]

    PostCloseUpdater._validate_instruments(instruments, expected)


@pytest.mark.parametrize(
    "instruments",
    [
        [_identity("TPE", "2330", 1), _identity("TWO", "4979", 2)],
        [
            _identity("TPE", "2330", 1),
            _identity("TPE", "2330", 2),
            _identity("TWO", "4979", 3),
        ],
        [
            _identity("TPE", "2330", 1),
            _identity("TPE", "6806", 2),
            _identity("TWO", "4979", 3),
        ],
    ],
)
def test_post_close_universe_validation_fails_closed_for_missing_duplicate_or_delisted(
    instruments,
):
    with pytest.raises(PostClosePreconditionError) as exc_info:
        PostCloseUpdater._validate_instruments(
            instruments,
            {"TPE": ("2330", "2317"), "TWO": ("4979",)},
        )

    assert exc_info.value.code == "DATE_EFFECTIVE_UNIVERSE_MISMATCH"


def test_post_close_cli_defers_tracking_mutation_until_after_reference_precondition():
    source = Path(__file__).parents[1] / "src/topicpilot_api/live/cli.py"
    text = source.read_text(encoding="utf-8")

    assert 'if decision != "POST_CLOSE":' in text
    assert "repository.refresh_tracking_universe()" in text
    assert "load_g2_preflight_context" in (
        Path(__file__).parents[1]
        / "src/topicpilot_api/live/post_close.py"
    ).read_text(encoding="utf-8")


def test_post_close_materializes_formal_pit_state_before_shadow_lifecycle():
    source = (
        Path(__file__).parents[1] / "src/topicpilot_api/live/post_close.py"
    ).read_text(encoding="utf-8")

    assert "materialize_bounded_formal_dates" in source
    assert 'dates=(snapshot_date,)' in source
    assert "TopicLifecycleEngine(self.session).run_once" in source
    assert 'result["formalTopicDailyState"]' in source


def test_post_close_completed_attempt_summary_is_recovery_safe():
    instrument_ids = [uuid4(), uuid4()]
    attempts = [
        SimpleNamespace(
            instrument_id=instrument_ids[0],
            updated_at=datetime(2026, 8, 30, 1, 0, tzinfo=UTC),
            id=uuid4(),
            status="SUCCESS",
            retry_count=1,
            error_code=None,
        ),
        SimpleNamespace(
            instrument_id=instrument_ids[1],
            updated_at=datetime(2026, 8, 30, 1, 1, tzinfo=UTC),
            id=uuid4(),
            status="SKIPPED",
            retry_count=0,
            error_code="MISSING_MARKET_DATA",
        ),
    ]

    class ScalarResult:
        def all(self):
            return attempts

    updater = PostCloseUpdater.__new__(PostCloseUpdater)
    updater.session = SimpleNamespace(scalars=lambda _query: ScalarResult())

    summary = updater._completed_attempt_summary("run-id", instrument_ids)

    assert summary == {
        "success_count": 1,
        "failure_count": 0,
        "skipped_count": 1,
        "retry_count": 1,
        "failure_codes": ("MISSING_MARKET_DATA",),
    }


def test_post_close_recent_run_is_not_considered_stale():
    run = SimpleNamespace(
        heartbeat_at=datetime(2026, 8, 30, 1, 0, 30, tzinfo=UTC),
    )

    assert PostCloseUpdater._is_recent_run(
        run,
        datetime(2026, 8, 30, 1, 1, tzinfo=UTC),
        stale_after=60,
    )
