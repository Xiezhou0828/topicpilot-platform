"""Synthetic contract tests: never call official endpoints or Production."""

from copy import deepcopy
from dataclasses import replace
from datetime import UTC, date, datetime
from decimal import Decimal
from hashlib import sha256
from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit
from uuid import uuid4

import pytest

from topicpilot_api import home_v2_publication as home
from topicpilot_api.final_publication_cli import main
from topicpilot_api.live.config import LiveRuntimeConfig
from topicpilot_api.live.home_completion import (
    COMPLETION_KEY,
    FAILURE,
    TARGET,
    OwnerHomeCompletion,
    evaluate_home_completion,
    validate_market_facts,
)
from topicpilot_api.live.post_close import PostClosePreconditionError
from topicpilot_api.market_data.aggregate_contract import (
    TPEX_DAILY_AGGREGATE_SOURCE,
    TWSE_DAILY_AGGREGATE_SOURCE,
)
from topicpilot_api.market_data.index_contract import IndexDataStatus, fetch_official_market_indexes

NOW = datetime(2026, 10, 4, tzinfo=UTC)


def completed_execution():
    owner_id = uuid4()
    key = f"post-close:ref:TW_MARKET:{TARGET}:NORMAL_CURRENT_DAY:FULL:OWNER_EXECUTION:{owner_id}"
    run = SimpleNamespace(
        id=uuid4(),
        run_type="POST_CLOSE",
        status="PARTIAL",
        completed_at=NOW,
        failure_code=FAILURE,
        failure_count=0,
        requested_count=553,
        success_count=553,
        metadata_payload={
            "runDate": TARGET.isoformat(),
            "executionScope": "NORMAL_CURRENT_DAY",
            "scope": "FULL",
            "executionMode": "MANUAL",
            "executionKey": key,
            "failureCodes": [FAILURE],
            "providerPointCount": 552,
            "ownerNormalExecution": {
                "authorization": "EXPLICIT_OWNER_ONCE",
                "executionId": str(owner_id),
                "reentryAllowed": False,
                "previousRunUntouched": True,
            },
            "statusResolutionMetrics": {
                "LEGITIMATE_UNAVAILABLE_COUNT": 1,
                "UNRESOLVED_UNAVAILABLE_COUNT": 0,
                "STATUS_AUTHORITY_PROVIDER_FAILURE_COUNT": 0,
                "STATUS_AUTHORITY_MANUAL_OVERRIDE_COUNT": 0,
            },
            "topicSnapshot": {
                "formalTopicDailyState": {"status": "SUCCESS"},
                "formalTopicSnapshotReadback": {"status": "PASS"},
            },
        },
    )
    cps = []
    for batch_key, state in [
        ("SESSION_VALIDATION", "COMPLETED"),
        ("INPUT_READINESS", "COMPLETED"),
        ("STATUS_RESOLUTION", "COMPLETED"),
        ("FORMAL_MARKET_FACTS:OFFICIAL", "COMPLETED"),
        ("A9_B2_FORMAL_PROCESSING", "COMPLETED"),
        ("FINAL_PUBLICATION", "FAILED"),
        ("COMPLETION", "PARTIAL"),
        ("FORMAL_MARKET_FACTS:TPE:1", "PARTIAL"),
        ("FORMAL_MARKET_FACTS:TWO:2", "COMPLETED"),
    ]:
        ingestion = batch_key.startswith(("FORMAL_MARKET_FACTS:TPE:", "FORMAL_MARKET_FACTS:TWO:"))
        success = 346 if "TPE:" in batch_key else 206 if "TWO:" in batch_key else 0
        skipped = 1 if "TPE:" in batch_key else 0
        cps.append(
            SimpleNamespace(
                run_id=run.id,
                batch_key=batch_key,
                status=state,
                attempt_number=1,
                checkpoint_hash=sha256(batch_key.encode()).hexdigest(),
                failed_count=0,
                provider_request_count=success if ingestion else None,
                provider_failure_count=0 if ingestion else None,
                processed_count=success + skipped,
                succeeded_count=success,
                skipped_count=skipped,
                metadata_payload={
                    "executionScope": "NORMAL_CURRENT_DAY",
                    "executionKey": key,
                    "providerMetricsApplicability": "ACTUAL" if ingestion else "NOT_APPLICABLE",
                },
            )
        )
    return run, cps


def test_home_completion_reuses_only_completed_outputs_not_normal_execution():
    run, cps = completed_execution()
    before = deepcopy(run.metadata_payload)
    report = evaluate_home_completion(run, cps)
    assert report["status"] == "PASS"
    for field in (
        "normalReentryAllowed",
        "newCollectorRunAllowed",
        "providerIngestionAllowed",
        "comparatorApplyAllowed",
        "topicCalculationAllowed",
    ):
        assert report[field] is False
    assert report["separateOwnerAuthorizationRequired"] is True
    assert run.status == "PARTIAL" and run.metadata_payload == before


@pytest.mark.parametrize(
    "field,value",
    [
        ("status", "RUNNING"),
        ("status", "SUCCESS"),
        ("completed_at", None),
        ("failure_code", "EXCHANGE_EMPTY_PAYLOAD"),
        ("failure_count", 1),
        ("requested_count", 555),
        ("success_count", 552),
        ("run_type", "INTRADAY"),
    ],
)
def test_invalid_terminal_execution_is_never_reentered(field, value):
    run, cps = completed_execution()
    setattr(run, field, value)
    assert evaluate_home_completion(run, cps)["status"] == "BLOCKED"


@pytest.mark.parametrize(
    "field,value",
    [
        ("executionScope", "HISTORY_RECOVERY"),
        ("scope", "TARGETED"),
        ("executionMode", "RECOVERY"),
        ("runDate", "2026-10-01"),
        ("executionKey", None),
        ("providerPointCount", 553),
        ("failureCodes", ["EXCHANGE_NOT_READY"]),
    ],
)
def test_legacy_mixed_or_wrong_date_execution_stays_fail_closed(field, value):
    run, cps = completed_execution()
    run.metadata_payload[field] = value
    assert evaluate_home_completion(run, cps)["status"] == "BLOCKED"


@pytest.mark.parametrize(
    "field,value",
    [
        ("LEGITIMATE_UNAVAILABLE_COUNT", 0),
        ("UNRESOLVED_UNAVAILABLE_COUNT", 1),
        ("STATUS_AUTHORITY_PROVIDER_FAILURE_COUNT", 1),
        ("STATUS_AUTHORITY_MANUAL_OVERRIDE_COUNT", 1),
    ],
)
def test_unknown_missing_or_provider_status_failure_stays_blocking(field, value):
    run, cps = completed_execution()
    run.metadata_payload["statusResolutionMetrics"][field] = value
    assert evaluate_home_completion(run, cps)["status"] == "BLOCKED"


@pytest.mark.parametrize(
    "field,value",
    [
        ("status", "FAILED"),
        ("failed_count", 1),
        ("provider_failure_count", 1),
        ("provider_request_count", None),
        ("succeeded_count", 345),
        ("skipped_count", 2),
        ("attempt_number", 2),
        ("checkpoint_hash", "not-a-hash"),
    ],
)
def test_incomplete_or_noncontinuous_ingestion_never_reaches_home_writer(field, value):
    run, cps = completed_execution()
    setattr(cps[-2], field, value)
    assert evaluate_home_completion(run, cps)["status"] == "BLOCKED"


def test_prior_claim_even_failed_cannot_consume_a_second_authorization():
    run, cps = completed_execution()
    run.metadata_payload["ownerHomeCompletion"] = {
        "status": "FAILED",
        "authorizationId": str(uuid4()),
    }
    assert (
        "HOME_COMPLETION_AUTHORIZATION_ALREADY_CLAIMED"
        in evaluate_home_completion(run, cps)["reasonCodes"]
    )
    run.metadata_payload.pop("ownerHomeCompletion")
    cp = deepcopy(cps[0])
    cp.batch_key = COMPLETION_KEY
    cps.append(cp)
    assert evaluate_home_completion(run, cps)["status"] == "BLOCKED"


def test_formal_topic_and_non_provider_null_metrics_are_not_inferred_from_zero():
    run, cps = completed_execution()
    cps[3].provider_request_count = 0
    assert (
        "HOME_COMPLETION_NON_PROVIDER_METRICS_INVALID"
        in evaluate_home_completion(run, cps)["reasonCodes"]
    )
    cps[3].provider_request_count = None
    run.metadata_payload["topicSnapshot"]["formalTopicSnapshotReadback"]["status"] = "FAIL"
    assert (
        "HOME_COMPLETION_FORMAL_TOPIC_NOT_READY"
        in evaluate_home_completion(run, cps)["reasonCodes"]
    )


def market_facts():
    indices, aggregates = [], []
    for market, source in (("TPE", "TWSE"), ("TWO", "TPEx")):
        endpoint = (
            f"https://www.{source.lower()}.com.tw/"
            if market == "TPE"
            else "https://www.tpex.org.tw/"
        )
        indices.append(
            SimpleNamespace(
                market=market,
                trading_date=TARGET,
                data_status=IndexDataStatus.AVAILABLE,
                source_provider=source,
                value=Decimal(100),
                previous_close=Decimal(99),
                response_content_hash=sha256(market.encode()).hexdigest(),
                lineage="TEST_ONLY_SYNTHETIC",
                source_endpoint=endpoint,
            )
        )
        aggregates.append(
            SimpleNamespace(
                market=market,
                trading_date=TARGET,
                data_status="AVAILABLE",
                source=TWSE_DAILY_AGGREGATE_SOURCE
                if market == "TPE"
                else TPEX_DAILY_AGGREGATE_SOURCE,
                response_content_hash=sha256(source.encode()).hexdigest(),
                lineage="TEST_ONLY_SYNTHETIC",
            )
        )
    return indices, aggregates


def parsed_official_index_pair():
    """Exercise the real adapters with controlled synthetic responses, never HTTP."""
    import json

    from test_task025_reconstructed_scope import payload

    def transport(url, _timeout):
        if "afterTrading/MI_INDEX" in url:
            assert parse_qs(urlsplit(url).query)["date"] == ["20261002"]
            return json.dumps(payload()).encode()
        if "MI_5MINS_HIST" in url:
            return b'{"fixtureClassification":"TEST_ONLY_SYNTHETIC","data":[]}'
        assert url == "https://www.tpex.org.tw/openapi/v1/tpex_index"
        return json.dumps(
            [
                {
                    "fixtureClassification": "TEST_ONLY_SYNTHETIC_NOT_MARKET_DATA",
                    "Date": "20261002",
                    "Open": "99",
                    "High": "101",
                    "Low": "98",
                    "Close": "100",
                    "Change": "2",
                }
            ]
        ).encode()

    return fetch_official_market_indexes(
        target_date=TARGET, retrieved_at=NOW, as_of=NOW, transport=transport
    )


def test_home_completion_accepts_exact_provider_identity_from_real_index_adapters():
    indices = parsed_official_index_pair()
    _, aggregates = market_facts()
    assert [f.source_provider for f in indices] == ["TWSE", "TPEx"]
    assert all(f.data_status == IndexDataStatus.AVAILABLE for f in indices)
    assert all(f.trading_date == TARGET and f.response_content_hash for f in indices)
    assert indices[1].previous_close == Decimal(98)
    validate_market_facts(indices, aggregates)


@pytest.mark.parametrize("provider", ["TPEX", "tpex", "RESEARCH", "SHADOW", "TWSE"])
def test_home_completion_rejects_noncontract_tpex_provider_identity(provider):
    indices = parsed_official_index_pair()
    _, aggregates = market_facts()
    indices = (indices[0], replace(indices[1], source_provider=provider))
    with pytest.raises(PostClosePreconditionError, match="HOME_COMPLETION_INDEX_NOT_READY"):
        validate_market_facts(indices, aggregates)


@pytest.mark.parametrize(
    "field,value",
    [
        ("trading_date", date(2026, 10, 1)),
        ("data_status", IndexDataStatus.UNAVAILABLE),
        ("source_endpoint", "https://research.example/"),
        ("response_content_hash", None),
        ("lineage", None),
        ("previous_close", Decimal(0)),
    ],
)
def test_real_tpex_adapter_does_not_bypass_date_authority_or_comparator_gate(field, value):
    indices = parsed_official_index_pair()
    _, aggregates = market_facts()
    indices = (indices[0], replace(indices[1], **{field: value}))
    with pytest.raises(PostClosePreconditionError, match="HOME_COMPLETION_INDEX_NOT_READY"):
        validate_market_facts(indices, aggregates)


@pytest.mark.parametrize(
    "value", [None, Decimal(0), Decimal(-1), Decimal("NaN"), Decimal("Infinity"), 100.0]
)
def test_index_missing_invalid_or_untyped_numeric_is_not_filled(value):
    indices, aggregates = market_facts()
    indices[0].value = value
    with pytest.raises(PostClosePreconditionError, match="INDEX_NOT_READY"):
        validate_market_facts(indices, aggregates)


@pytest.mark.parametrize(
    "field,value",
    [
        ("trading_date", date(2026, 10, 1)),
        ("data_status", IndexDataStatus.UNAVAILABLE),
        ("source_provider", "RESEARCH"),
        ("source_endpoint", "https://research.example/"),
        ("response_content_hash", None),
        ("response_content_hash", "unverified"),
        ("lineage", None),
        ("previous_close", Decimal(0)),
    ],
)
def test_wrong_date_or_nonformal_index_authority_stays_blocking(field, value):
    indices, aggregates = market_facts()
    setattr(indices[0], field, value)
    with pytest.raises(PostClosePreconditionError):
        validate_market_facts(indices, aggregates)


def test_official_pair_and_aggregates_are_required_without_policy_relaxation():
    indices, aggregates = market_facts()
    validate_market_facts(indices, aggregates)
    for missing in ([], indices[:1], [indices[0], indices[0]]):
        with pytest.raises(PostClosePreconditionError):
            validate_market_facts(missing, aggregates)
    aggregates[1].trading_date = date(2026, 10, 1)
    with pytest.raises(PostClosePreconditionError, match="AGGREGATE_NOT_READY"):
        validate_market_facts(indices, aggregates)


def test_taiex_transport_requires_explicit_index_report_type(monkeypatch):
    import json

    from test_task025_reconstructed_scope import DAY, NOW, payload

    def transport(url, _timeout):
        if "afterTrading/MI_INDEX" in url:
            query = parse_qs(urlsplit(url).query)
            body = payload()
            # Match the real response shape: omitted type -> table placeholders.
            if query.get("type") != ["IND"]:
                body["tables"] = [{} for _ in range(10)]
            assert query.get("date") == ["20261002"]
            return json.dumps(body).encode()
        return b"[]"

    fact = fetch_official_market_indexes(
        target_date=DAY, retrieved_at=NOW, as_of=NOW, transport=transport
    )[0]
    assert fact.data_status == IndexDataStatus.AVAILABLE
    assert fact.previous_close == Decimal(98)
    assert "type=IND" in fact.source_endpoint
    assert (fact.open, fact.high, fact.low) == (None, None, None)


def test_home_breadth_uses_execution_identity_not_price_availability(monkeypatch):
    price_id, unavailable_id, excluded_id = uuid4(), uuid4(), uuid4()
    rows = [
        {
            "instrument_id": price_id,
            "market": "TPE",
            "symbol": "TEST1",
            "status_code": "NORMAL",
            "close": Decimal(10),
            "previous_close": Decimal(9),
            "observed_at": NOW,
        },
        {
            "instrument_id": unavailable_id,
            "market": "TPE",
            "symbol": "2601",
            "status_code": "SUSPENDED",
            "close": None,
            "previous_close": None,
            "observed_at": None,
        },
        {
            "instrument_id": excluded_id,
            "market": "TPE",
            "symbol": "TEST3",
            "status_code": "UNKNOWN",
            "close": None,
            "previous_close": None,
            "observed_at": None,
        },
    ]
    received = []

    def read_rows(_session, _day, *, expected_instrument_ids=None):
        received.append(expected_instrument_ids)
        return (
            rows
            if expected_instrument_ids is None
            else [r for r in rows if r["instrument_id"] in expected_instrument_ids]
        )

    monkeypatch.setattr(home, "read_daily_market_rows", read_rows)
    _, _, observations = home._breadth(
        None, TARGET, expected_instrument_ids=(price_id, unavailable_id)
    )
    assert received == [(price_id, unavailable_id)]
    assert {r["instrument_id"] for r in observations} == {price_id, unavailable_id}
    assert observations[1]["close"] is None
    distribution = home.build_market_distribution(observations, eligible_count=2, as_of=NOW)
    assert distribution["eligible"] == 1 and distribution["excluded"] == 1


@pytest.mark.parametrize("ids", [(), ("duplicate", "duplicate")])
def test_empty_or_duplicate_home_execution_universe_fails_before_any_write(ids):
    with pytest.raises(ValueError, match="HOME_EXECUTION_UNIVERSE_INVALID"):
        home.materialize_home_v2(None, trading_date=TARGET, expected_instrument_ids=ids)


def test_home_completion_cli_requires_separate_explicit_authorization():
    with pytest.raises(SystemExit, match="EXPLICIT_OWNER_AUTHORIZATION_REQUIRED"):
        main(
            [
                "--operation",
                "home-completion-apply",
                "--target-date",
                str(TARGET),
                "--expected-sha",
                "test",
            ]
        )


def test_home_completion_cannot_expand_target_date_even_with_authorization():
    with pytest.raises(SystemExit, match="TARGET_DATE_OUTSIDE_APPROVED_CLOSURE"):
        main(
            [
                "--operation",
                "home-completion-apply",
                "--target-date",
                "2026-10-01",
                "--expected-sha",
                "test",
                "--owner-authorized-once",
            ]
        )


@pytest.mark.parametrize(
    "invalid",
    [
        None,
        "context",
        "coverage",
        "previous_zero",
        "previous_date",
        "instrument",
        "authority",
        "lineage",
        "topic",
        "flow",
        "published",
        "reference",
    ],
)
def test_real_preflight_checks_exact_context_comparator_and_formal_readback(monkeypatch, invalid):
    from topicpilot_api.live import home_completion as module

    run, cps = completed_execution()
    ids = tuple(uuid4() for _ in range(553))
    prior = date(2026, 10, 1)
    rows = [
        dict(
            instrument_id=i,
            close=Decimal(10),
            previous_close=Decimal(9),
            previous_close_date=prior,
            previous_close_instrument_id=i,
            previous_close_source="TWSE_OFFICIAL_DAILY",
            previous_close_lineage="test-only",
        )
        for i in ids[:-1]
    ]
    rows.append(dict(instrument_id=ids[-1], close=None))
    context = SimpleNamespace(
        context_ready=invalid != "context",
        previous_session=prior,
        markets=(
            SimpleNamespace(
                instrument_codes=tuple(map(str, ids)), instrument_ids={str(i): str(i) for i in ids}
            ),
        ),
    )
    report = {
        "topicSnapshot": {"status": "FAIL" if invalid == "topic" else "PASS"},
        "institutionalFlow": {"status": "FAIL" if invalid == "flow" else "PASS"},
        "homePublication": {"status": "NOT_FOUND"},
    }

    class ReadOnlySession:
        def get(self, *_):
            return run

        def scalars(self, *_):
            return cps

        def scalar(self, *_):
            return uuid4() if invalid == "published" else None

    completion = OwnerHomeCompletion(
        ReadOnlySession(),
        LiveRuntimeConfig(reference_data_version="ref"),
        run_id=run.id,
        authorization_id=uuid4(),
    )
    monkeypatch.setattr(module, "load_g2_preflight_context", lambda *_a, **_kw: context)
    monkeypatch.setattr(
        module,
        "reconcile_daily_market",
        lambda *_a, **_kw: SimpleNamespace(downstream_ready=invalid != "coverage"),
    )
    monkeypatch.setattr(module, "read_daily_market_rows", lambda *_a, **_kw: rows)
    monkeypatch.setattr(completion, "_formal_publication_readback", lambda *_a, **_kw: report)
    fields = {
        "previous_zero": ("previous_close", Decimal(0)),
        "previous_date": ("previous_close_date", date(2026, 9, 30)),
        "instrument": ("previous_close_instrument_id", uuid4()),
        "authority": ("previous_close_source", "SHADOW"),
        "lineage": ("previous_close_lineage", None),
    }
    if invalid in fields:
        field, value = fields[invalid]
        rows[0][field] = value
    if invalid == "reference":
        completion.config = LiveRuntimeConfig(reference_data_version="wrong-ref")
    if invalid:
        with pytest.raises(PostClosePreconditionError):
            completion.preflight()
    else:
        result = completion.preflight()
        assert result["status"] == "PASS" and result["targetCount"] == 553
        assert result["priceCount"] == 552 and len(completion.expected_ids) == 553


@pytest.mark.parametrize("in_scope_status", ["SUSPENDED", "UNKNOWN", "MISSING_MARKET_DATA"])
def test_actual_home_writer_keeps_in_scope_failure_gate_and_excludes_only_execution_outsiders(
    monkeypatch,
    in_scope_status,
):
    from test_task025_reconstructed_scope import CaptureSession, fetch

    price_id, unavailable_id, excluded_id = uuid4(), uuid4(), uuid4()
    observations = [
        dict(
            instrument_id=price_id,
            market="TPE",
            symbol="TEST1",
            status_code="NORMAL",
            close=Decimal(10),
            previous_close=Decimal(9),
            observed_at=NOW,
        ),
        dict(
            instrument_id=unavailable_id,
            market="TPE",
            symbol="2601" if in_scope_status == "SUSPENDED" else "TEST_MISSING",
            status_code=in_scope_status,
            close=None,
            previous_close=None,
            observed_at=NOW,
        ),
        dict(
            instrument_id=excluded_id,
            market="TPE",
            symbol="OUTSIDE",
            status_code="UNKNOWN",
            close=None,
            previous_close=None,
            observed_at=None,
        ),
    ]

    def scoped_rows(_session, _date, *, expected_instrument_ids):
        assert set(expected_instrument_ids) == {price_id, unavailable_id}
        return [r for r in observations if r["instrument_id"] in expected_instrument_ids]

    monkeypatch.setattr(home, "read_daily_market_rows", scoped_rows)
    for name in ("_formal_topic_rows", "_formal_topic_history", "_read_formal_topic_signal_rows"):
        monkeypatch.setattr(home, name, lambda *_: [])
    monkeypatch.setattr(home, "_signal_history_with_authority", lambda *_a, **_kw: [])
    monkeypatch.setattr(home, "_read_home_institutional_flow", lambda *_: None)
    monkeypatch.setattr(home, "_read_previous_session_turnover", lambda *_: None)
    session = CaptureSession()
    result = home.materialize_home_v2(
        session,
        trading_date=TARGET,
        now=NOW,
        expected_instrument_ids=(price_id, unavailable_id),
        market_index_facts=[fetch()[0]],
        market_aggregate_facts=[],
    )
    assert result["publicationState"] == (
        "PUBLISHED" if in_scope_status == "SUSPENDED" else "UNAVAILABLE"
    )
