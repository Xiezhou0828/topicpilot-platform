from datetime import date
from pathlib import Path

from topicpilot_api.daily_market import assess_daily_coverage

MIGRATION = (
    Path(__file__).parents[1]
    / "alembic"
    / "versions"
    / "0025_task_data_022_daily_market_contract.py"
)


def test_full_tpe_two_coverage_is_downstream_ready():
    result = assess_daily_coverage(
        trade_date=date(2026, 8, 12),
        expected_by_market={"TPE": 300, "TWO": 207},
        observed_by_market={"TPE": 300, "TWO": 207},
        priced_by_market={"TPE": 300, "TWO": 207},
    )

    assert result.status == "READY"
    assert result.downstream_ready is True
    assert result.expected_count == 507
    assert result.coverage_pct == 100.0
    assert result.reason_codes == ()


def test_partial_market_failure_fails_closed():
    result = assess_daily_coverage(
        trade_date=date(2026, 8, 12),
        expected_by_market={"TPE": 300, "TWO": 207},
        observed_by_market={"TPE": 300, "TWO": 150},
    )

    assert result.status == "PARTIAL"
    assert result.downstream_ready is False
    assert "INCOMPLETE_COVERAGE" in result.reason_codes
    assert "TWO_INCOMPLETE" in result.reason_codes


def test_approved_no_trade_is_covered_but_unpriced_and_ready():
    result = assess_daily_coverage(
        trade_date=date(2026, 8, 12),
        expected_by_market={"TPE": 507},
        observed_by_market={"TPE": 507},
        priced_by_market={"TPE": 506},
        covered_by_market={"TPE": 507},
    )

    assert result.expected_count == 507
    assert result.observed_count == 507
    assert result.priced_count == 506
    assert result.covered_count == 507
    assert result.unavailable_count == 1
    assert result.unexplained_missing_count == 0
    assert result.status == "READY"
    assert result.downstream_ready is True
    assert "APPROVED_NO_TRADE_COVERAGE" in result.reason_codes


def test_unknown_missing_is_not_covered_even_when_observed_row_exists():
    result = assess_daily_coverage(
        trade_date=date(2026, 8, 12),
        expected_by_market={"TPE": 507},
        observed_by_market={"TPE": 507},
        priced_by_market={"TPE": 506},
        covered_by_market={"TPE": 506},
    )

    assert result.covered_count == 506
    assert result.unexplained_missing_count == 1
    assert result.status == "PARTIAL"
    assert result.downstream_ready is False
    assert "UNEXPLAINED_MISSING_DATA" in result.reason_codes


def test_null_close_is_unavailable_and_never_coerced_to_zero():
    result = assess_daily_coverage(
        trade_date=date(2026, 8, 12),
        expected_by_market={"TPE": 1},
        observed_by_market={"TPE": 1},
        priced_by_market={"TPE": 0},
    )

    assert result.observed_count == 1
    assert result.priced_count == 0
    assert result.unavailable_count == 1
    assert result.downstream_ready is False
    assert "UNAVAILABLE_DAILY_CLOSE" in result.reason_codes


def test_date_or_stable_key_conflict_blocks_handoff():
    result = assess_daily_coverage(
        trade_date=date(2026, 8, 12),
        expected_by_market={"TPE": 1},
        observed_by_market={"TPE": 1},
        wrong_date_count=1,
        duplicate_key_count=1,
    )

    assert result.downstream_ready is False
    assert "DATA_DATE_MISMATCH" in result.reason_codes
    assert "DUPLICATE_STABLE_KEY" in result.reason_codes


def test_non_trading_day_is_explicit_and_not_downstream_ready():
    result = assess_daily_coverage(
        trade_date=date(2026, 8, 9),
        expected_by_market={"TPE": 300, "TWO": 207},
        observed_by_market={},
        market_closed=True,
    )

    assert result.status == "MARKET_CLOSED"
    assert result.downstream_ready is False
    assert result.reason_codes[0] == "MARKET_CLOSED"


def test_daily_projection_migration_is_additive_and_uses_canonical_chain():
    source = MIGRATION.read_text(encoding="utf-8")

    assert 'down_revision = "0024_task_be_007_topic_snapshots"' in source
    assert "CREATE VIEW topicpilot.vw_daily_market_observations" in source
    assert "topicpilot.canonical_observations" in source
    assert "topicpilot.canonical_price_observations" in source
    assert "market_code || ':' || instrument_code || ':' || trade_date::text" in source
    assert "DROP TABLE" not in source


def test_no_trade_migration_projects_status_and_never_zero_fills():
    migration = MIGRATION.with_name("0026_task_data_022a_no_trade_coverage.py")
    source = migration.read_text(encoding="utf-8")

    assert "canonical_trading_status_observations" in source
    assert "EXCHANGE_CONFIRMED_NO_DATA" in source
    assert "close IS NOT NULL OR status_code IN" in source
    assert "COALESCE(ts.status_code, 'UNKNOWN')" in source
    assert "close = 0" not in source
    assert "DROP TABLE" not in source
