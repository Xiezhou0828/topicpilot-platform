"""Controlled fixtures only: receipt closure cannot repeat a production writer."""

from copy import deepcopy
from uuid import uuid4

import pytest
from test_home_only_completion import NOW, completed_execution

from topicpilot_api.live.config import LiveRuntimeConfig
from topicpilot_api.live.home_completion import COMPLETION_KEY
from topicpilot_api.live.home_receipt import RECEIPT_KEY, OwnerPublishedHomeReceipt
from topicpilot_api.live.post_close import PostClosePreconditionError
from topicpilot_api.orm import HomePublication


def fixture_receipt():
    from types import SimpleNamespace

    run, cps = completed_execution()
    completion_id, authorization_id, publication_id = uuid4(), uuid4(), uuid4()
    failure = dict(
        authorizationId=str(completion_id),
        operation="HOME_ONLY_COMPLETION",
        status="FAILED",
        exceptionClass="TypeError",
        failureCode="HOME_COMPLETION_ORCHESTRATION_FAILURE",
        previousState="PARTIAL",
        previousFailureCode=run.failure_code,
        previousFailureCodes=[run.failure_code],
        reentryAllowed=False,
        normalExecutionRepeated=False,
        providerIngestionRepeated=False,
    )
    run.metadata_payload["ownerHomeCompletion"] = failure
    readback = {
        "status": "PASS",
        "homePublication": {"status": "PASS", "publicationId": str(publication_id)},
        "topicSnapshot": {"status": "PASS"},
        "institutionalFlow": {"status": "PASS"},
    }
    for key in ("FINAL_PUBLICATION", "COMPLETION"):
        cp = deepcopy(next(c for c in cps if c.batch_key == key))
        cp.attempt_number, cp.status = 2, "COMPLETED"
        cp.metadata_payload["formalPublication" if key == "FINAL_PUBLICATION" else "readback"] = (
            readback
        )
        cps.append(cp)
    for number, status in enumerate(("IN_PROGRESS", "COMPLETED", "FAILED"), 1):
        cp = deepcopy(cps[0])
        cp.batch_key, cp.attempt_number, cp.status = COMPLETION_KEY, number, status
        cp.metadata_payload.update(failure)
        cps.append(cp)
    home = SimpleNamespace(
        id=publication_id,
        trading_date=NOW.date().replace(day=2),
        source_run_id=str(run.id),
        published_at=NOW,
        lineage_hash="test-only",
        source_dataset_id="TEST_ONLY_SYNTHETIC",
    )

    class ReadSession:
        def get(self, *_):
            return run

        def scalars(self, query):
            return [home] if query.column_descriptions[0]["entity"] == HomePublication else cps

    receipt = OwnerPublishedHomeReceipt(
        ReadSession(),
        LiveRuntimeConfig(reference_data_version="ref"),
        run_id=run.id,
        publication_id=publication_id,
        completion_id=completion_id,
        authorization_id=authorization_id,
    )
    receipt._formal_publication_readback = lambda *_a, **_kw: readback
    return receipt, run, cps, home, readback


def test_receipt_preflight_is_read_only_and_never_uses_home_writer():
    receipt, run, cps, home, _ = fixture_receipt()
    before = deepcopy((vars(run), [vars(cp) for cp in cps], vars(home)))
    report = receipt.preflight()
    assert report["status"] == "PASS" and not report["alreadyFinalized"]
    assert not report["homeWriterAllowed"] and not report["providerIngestionAllowed"]
    assert not report["normalReentryAllowed"]
    assert (vars(run), [vars(cp) for cp in cps], vars(home)) == before


@pytest.mark.parametrize(
    "field,value",
    [
        ("exceptionClass", "ValueError"),
        ("failureCode", "PROVIDER_FAILURE"),
        ("status", "CLAIMED"),
        ("previousState", "RUNNING"),
        ("reentryAllowed", True),
        ("authorizationId", "wrong"),
        ("providerIngestionRepeated", True),
        ("normalExecutionRepeated", True),
    ],
)
def test_receipt_wrong_or_unproven_failure_claim_is_blocked(field, value):
    receipt, run, *_ = fixture_receipt()
    run.metadata_payload["ownerHomeCompletion"][field] = value
    with pytest.raises(PostClosePreconditionError):
        receipt.preflight()


@pytest.mark.parametrize(
    "failure",
    [
        "run",
        "key",
        "continuity",
        "home-event",
        "final-event",
        "provider",
        "scope",
        "home",
        "source",
        "lineage",
        "readback",
    ],
)
def test_receipt_never_closes_missing_or_mismatched_committed_evidence(failure):
    receipt, run, cps, home, readback = fixture_receipt()
    if failure == "run":
        run.status = "RUNNING"
    elif failure == "key":
        run.metadata_payload["executionKey"] = "wrong"
    elif failure == "continuity":
        cps[-1].attempt_number = 7
    elif failure == "home-event":
        cps[-1].status = "COMPLETED"
    elif failure == "final-event":
        cps[-4].metadata_payload["readback"] = {}
    elif failure == "provider":
        next(
            c for c in cps if c.batch_key.startswith("FORMAL_MARKET_FACTS:TWO:")
        ).provider_failure_count = 1
    elif failure == "scope":
        run.metadata_payload["executionScope"] = "HISTORY_RECOVERY"
    elif failure == "home":
        home.id = uuid4()
    elif failure == "source":
        home.source_run_id = str(uuid4())
    elif failure == "lineage":
        home.lineage_hash = None
    else:
        readback["status"] = "FAIL"
    with pytest.raises(PostClosePreconditionError):
        receipt.preflight()


def test_receipt_cli_requires_new_explicit_authorization_without_reusing_home_claim():
    from topicpilot_api.final_publication_cli import main

    with pytest.raises(SystemExit, match="EXPLICIT_OWNER_AUTHORIZATION_REQUIRED"):
        main(
            [
                "--operation",
                "home-receipt-apply",
                "--target-date",
                "2026-10-02",
                "--expected-sha",
                "test",
            ]
        )


def test_receipt_surface_has_no_provider_or_home_write_path():
    import inspect

    source = inspect.getsource(OwnerPublishedHomeReceipt)
    for forbidden in ("materialize_home_v2(", "run_once(", "fetch_official", "persist_comparator("):
        assert forbidden not in source
    assert RECEIPT_KEY != COMPLETION_KEY
