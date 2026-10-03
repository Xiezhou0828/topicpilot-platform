from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, date, datetime
from decimal import Decimal
from hashlib import sha256
from types import SimpleNamespace
from urllib.error import URLError
from uuid import uuid4

import pytest

from topicpilot_api.comparator import (
    ComparatorError,
    ComparatorPlan,
    ComparatorPoint,
    _ComparatorMapper,
    validate_point,
)
from topicpilot_api.final_publication_cli import main
from topicpilot_api.live.normal_execution import OwnerNormalExecution, evaluate_normal_identity
from topicpilot_api.live.post_close import PostClosePreconditionError
from topicpilot_api.market_data.exchange import _json
from topicpilot_api.market_data.history import HistoricalBar, HistoricalProviderError
from topicpilot_api.market_data.receipt import ResponseBytes
from topicpilot_api.normalizer.contracts import InputEnvelope, MappingPolicy, ReferenceContext
from topicpilot_api.provider_preflight import _provider_failure

PRIOR = date(2026, 10, 1)
TARGET = date(2026, 10, 2)
NOW = datetime(2026, 10, 4, tzinfo=UTC)


def point():
    raw = json.dumps({"stat": "OK", "date": "20261001"}).encode()
    return ComparatorPoint(
        uuid4(),
        "2330",
        "TPE",
        HistoricalBar(PRIOR, Decimal(100), Decimal(103), Decimal(99), Decimal(102), Decimal(1000)),
        {
            "endpoint": "https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?date=20261001",
            "responseDate": "20261001",
            "payloadSize": len(raw),
            "payloadHash": sha256(raw).hexdigest(),
            "rawStatus": "OK",
            "classification": None,
            "httpStatus": 200,
        },
        NOW,
    )


def test_comparator_identity_does_not_depend_on_retrieval_time():
    p = point()
    assert p.identity == replace(p, retrieved_at=datetime(2026, 10, 5, tzinfo=UTC)).identity
    assert p.identity != replace(p, bar=replace(p.bar, close=Decimal(101))).identity
    assert p.identity != replace(p, instrument_id=uuid4()).identity
    assert (
        p.identity
        != replace(p, receipt={**p.receipt, "payloadHash": sha256(b"new").hexdigest()}).identity
    )


@pytest.mark.parametrize("value", [None, Decimal(0), Decimal("NaN"), Decimal("Infinity")])
def test_comparator_never_fills_missing_or_invalid_close(value):
    p = point()
    with pytest.raises(ComparatorError, match="PRICE_NOT_ACCEPTED"):
        validate_point(replace(p, bar=replace(p.bar, close=value)), PRIOR)


@pytest.mark.parametrize(
    "override",
    [
        {"responseDate": "20260930"},
        {"payloadHash": ""},
        {"payloadSize": 0},
        {"endpoint": "https://research.example/test"},
        {"rawStatus": "not ready"},
    ],
)
def test_comparator_provenance_fail_closed(override):
    p = point()
    with pytest.raises(ComparatorError, match="PROVENANCE_INVALID"):
        validate_point(replace(p, receipt={**p.receipt, **override}), PRIOR)


def test_comparator_mapper_emits_price_only_and_preserves_null_semantics():
    p = point()
    envelope = InputEnvelope(
        p.payload(), p.instrument_id, uuid4(), uuid4(), uuid4(), NOW, NOW, NOW, "2026-10-01"
    )
    ref = ReferenceContext("test", "Asia/Taipei", "REGULAR", "TW_MARKET", "TWD", 2)
    result = _ComparatorMapper()(envelope, ref, MappingPolicy())
    assert [c.family_code for c in result.candidates] == ["PRICE"]
    assert result.candidates[0].quality_state == "ACCEPTED"
    assert result.candidates[0].values["close"] == Decimal(102)
    assert p.payload()["volume"] is None


def old_run():
    return SimpleNamespace(
        id=uuid4(),
        status="PARTIAL",
        completed_at=NOW,
        heartbeat_at=NOW,
        metadata_payload={
            "runDate": TARGET.isoformat(),
            "scope": "FULL",
            "executionMode": "MANUAL",
            "executionKey": f"post-close:ref:TW_MARKET:{TARGET}:FULL",
        },
    )


def checkpoints(old):
    return [
        SimpleNamespace(
            run_id=old.id,
            batch_key="FORMAL_MARKET_FACTS:TPE:1",
            attempt_number=i,
            checkpoint_hash=sha256(str(i).encode()).hexdigest(),
            status="FAILED" if i == 2 else "IN_PROGRESS",
            metadata_payload={},
        )
        for i in (1, 2)
    ] + [
        SimpleNamespace(
            run_id=old.id,
            batch_key="COMPLETION",
            attempt_number=1,
            checkpoint_hash=sha256(b"completion").hexdigest(),
            status="PARTIAL",
            metadata_payload={},
        )
    ]


def evaluate(old, runs=None, cps=None):
    return evaluate_normal_identity(
        [old] if runs is None else runs,
        checkpoints(old) if cps is None else cps,
        run_date=TARGET,
        supersedes_run_id=old.id,
        reference_version="ref",
        calendar_code="TW_MARKET",
    )


def test_terminal_legacy_run_can_authorize_fresh_normal_without_reuse_or_mutation():
    old = old_run()
    before = dict(old.metadata_payload)
    report = evaluate(old)
    assert report["status"] == "PASS"
    assert report["completedCheckpointReuse"] == "NONE"
    assert report["oldRunMutationAllowed"] is False
    assert report["newRecoveryRunAllowed"] is False
    assert old.metadata_payload == before and old.status == "PARTIAL"


@pytest.mark.parametrize("status", ["RUNNING", "SUCCESS", "MARKET_CLOSED"])
def test_new_normal_rejects_active_or_already_published_date(status):
    old = old_run()
    old.status = status
    assert evaluate(old)["status"] == "BLOCKED"


def test_new_normal_rejects_broken_checkpoint_continuity_and_unknown_scope():
    old = old_run()
    cps = checkpoints(old)
    cps[1].attempt_number = 3
    assert evaluate(old, cps=cps)["status"] == "BLOCKED"
    old.metadata_payload["executionScope"] = "HISTORY_RECOVERY"
    assert evaluate(old)["status"] == "BLOCKED"
    old.metadata_payload.pop("executionKey")
    assert evaluate(old)["status"] == "BLOCKED"


def test_duplicate_new_identity_cannot_consume_another_authorization():
    old = old_run()
    successor = old_run()
    successor.metadata_payload["executionKey"] += f":OWNER_EXECUTION:{uuid4()}"
    assert (
        "OWNER_NORMAL_AUTHORIZATION_ALREADY_CLAIMED"
        in evaluate(old, runs=[old, successor])["reasonCodes"]
    )


def test_owner_normal_key_is_separate_and_never_targets_recovery():
    updater = OwnerNormalExecution.__new__(OwnerNormalExecution)
    updater.config = SimpleNamespace(reference_data_version="ref", calendar_code="TW_MARKET")
    updater.execution_id = uuid4()
    key = updater._execution_key(TARGET)
    assert key.startswith(f"post-close:ref:TW_MARKET:{TARGET}:NORMAL_CURRENT_DAY:FULL:")
    assert str(updater.execution_id) in key
    for mode in ("RECOVERY", "SCHEDULED"):
        with pytest.raises(PostClosePreconditionError):
            updater._execution_key(TARGET, execution_mode=mode)
    with pytest.raises(PostClosePreconditionError):
        updater._execution_key(TARGET, target_symbols=("2601",))


def test_receipt_keeps_actual_http_status_hash_size_date_and_raw_status():
    raw = ResponseBytes(b'{"date":"20261002","stat":"ok"}')
    raw.http_status = 200
    evidence = {}
    assert _json(lambda *_: raw, "https://www.tpex.org.tw/test", 10, evidence)["date"] == "20261002"
    assert evidence["httpStatus"] == 200
    assert evidence["payloadHash"] == sha256(raw).hexdigest()
    assert evidence["payloadSize"] == len(raw)
    assert evidence["stage"] == "DATASET_PARSE"


def test_transport_failure_is_not_json_decode_or_date_match():
    def fail(*_):
        raise URLError("transport failed")

    with pytest.raises(HistoricalProviderError) as exc:
        _json(fail, "https://www.tpex.org.tw/test", 10, {})
    assert exc.value.evidence["classification"] == "PROVIDER_TRANSPORT_FAILURE"
    assert exc.value.evidence["stage"] == "TRANSPORT"
    assert _provider_failure(exc.value).target_date_matched is False


@pytest.mark.parametrize("raw", [b"<html>not JSON</html>", b"\xff", b"null"])
def test_json_or_shape_rejection_retains_receipt_and_is_fail_closed(raw):
    with pytest.raises(HistoricalProviderError) as exc:
        _json(lambda *_: raw, "https://www.tpex.org.tw/test", 10, {})
    assert exc.value.code == "INVALID_PAYLOAD"
    assert exc.value.evidence["payloadHash"] == sha256(raw).hexdigest()
    assert exc.value.evidence["classification"] == "PROVIDER_PAYLOAD_SCHEMA_CHANGE"
    assert _provider_failure(exc.value).payload_parsed is False
    assert _provider_failure(exc.value).target_date_matched is False


@pytest.mark.parametrize("operation", ["normal-run", "comparator-apply"])
def test_cli_write_requires_explicit_owner_authorization_before_database(operation):
    with pytest.raises(SystemExit, match="EXPLICIT_OWNER_AUTHORIZATION_REQUIRED"):
        main(
            [
                "--operation",
                operation,
                "--target-date",
                TARGET.isoformat(),
                "--expected-sha",
                "none",
            ]
        )


def test_cli_cannot_turn_into_historical_backfill():
    with pytest.raises(SystemExit, match="TARGET_DATE_OUTSIDE_APPROVED_CLOSURE"):
        main(
            [
                "--operation",
                "normal-preflight",
                "--target-date",
                "2026-09-30",
                "--expected-sha",
                "none",
            ]
        )


def test_552_price_and_one_unavailable_are_separate_accounted_targets():
    p = point()
    points = tuple(
        replace(p, instrument_id=uuid4(), code=str(1000 + i), market="TPE" if i < 346 else "TWO")
        for i in range(552)
    )
    plan = ComparatorPlan(
        PRIOR,
        TARGET,
        "ref",
        points,
        ({"symbol": "2601", "resolvedStatus": "SUSPENDED", "isLegitimateUnavailable": True},),
    )
    result = plan.summary()
    assert result["accountedCount"] == 553 and result["priceCount"] == 552
    assert [m["priceCount"] for m in result["markets"]] == [346, 206]
    assert "2601" not in {p.code for p in plan.points}
