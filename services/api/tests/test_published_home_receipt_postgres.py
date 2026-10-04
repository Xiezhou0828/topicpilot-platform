"""Actual PostgreSQL JSONB/atomic receipt regression; no official or Production data."""

from copy import deepcopy
from uuid import uuid4

import pytest
from sqlalchemy import select
from test_home_only_completion import market_facts
from test_home_only_completion_postgres import completion_db as completion_db

from topicpilot_api.live.config import LiveRuntimeConfig
from topicpilot_api.live.home_receipt import RECEIPT_KEY, OwnerPublishedHomeReceipt
from topicpilot_api.live.post_close import PostClosePreconditionError
from topicpilot_api.orm import HomePublication, LiveCollectorCheckpoint


def committed_home_failed_receipt(completion_db, monkeypatch):
    session, completion, run, old, writes = completion_db
    # Reproduce the old metadata boundary with the actual psycopg JSONB codec.
    # The committed typed-date Home stays PUBLISHED after final metadata rollback.
    with monkeypatch.context() as legacy:
        legacy.setattr("topicpilot_api.live.home_completion._json_safe", lambda value: value)
        with pytest.raises(Exception, match="not JSON serializable"):
            completion.complete_once(indices=market_facts()[0], aggregates=market_facts()[1])
    session.refresh(run)
    assert (
        run.status == "PARTIAL"
        and run.metadata_payload["ownerHomeCompletion"]["status"] == "FAILED"
    )
    home = session.scalar(
        select(HomePublication).where(HomePublication.source_run_id == str(run.id))
    )
    assert home.publication_state == "PUBLISHED" and writes == [str(run.id)]
    receipt = OwnerPublishedHomeReceipt(
        session,
        LiveRuntimeConfig(reference_data_version="ref"),
        run_id=run.id,
        publication_id=home.id,
        completion_id=completion.authorization_id,
        authorization_id=uuid4(),
    )
    monkeypatch.setattr(
        receipt, "_formal_publication_readback", completion._formal_publication_readback
    )
    return session, receipt, run, old, home, writes


def test_actual_jsonb_receipt_is_atomic_idempotent_and_preserves_failed_home_history(
    completion_db, monkeypatch
):
    session, receipt, run, old, home, writes = committed_home_failed_receipt(
        completion_db, monkeypatch
    )
    failed = deepcopy(run.metadata_payload["ownerHomeCompletion"])
    original = {
        cp.id: (cp.checkpoint_hash, deepcopy(cp.metadata_payload), cp.status)
        for cp in session.scalars(
            select(LiveCollectorCheckpoint).where(LiveCollectorCheckpoint.run_id == run.id)
        )
    }
    home_before = deepcopy(home.payload), home.updated_at, home.lineage_hash, home.published_at
    assert receipt.preflight()["status"] == "PASS"
    result = receipt.complete_once()
    assert result["normalRunStatus"] == "SUCCESS" and result["productionMutated"]
    session.refresh(run)
    assert run.status == "SUCCESS" and run.requested_count == run.success_count == 553
    assert run.metadata_payload["ownerHomeCompletion"] == failed
    assert run.metadata_payload["ownerNormalExecution"]["reentryAllowed"] is False
    assert run.metadata_payload["topicSnapshot"]["homePublication"]["tradingDate"] == "2026-10-02"
    assert run.metadata_payload["ownerPublishedHomeReceipt"]["reentryAllowed"] is False
    cps = list(
        session.scalars(
            select(LiveCollectorCheckpoint).where(LiveCollectorCheckpoint.run_id == run.id)
        )
    )
    assert {
        cp.id: (cp.checkpoint_hash, cp.metadata_payload, cp.status)
        for cp in cps
        if cp.id in original
    } == original
    new = [cp for cp in cps if cp.id not in original]
    assert len(new) == 1 and new[0].batch_key == RECEIPT_KEY and new[0].status == "COMPLETED"
    assert new[0].provider_request_count is None and new[0].provider_failure_count is None
    session.refresh(home)
    assert (home.payload, home.updated_at, home.lineage_hash, home.published_at) == home_before
    assert writes == [str(run.id)]
    assert receipt.complete_once()["productionMutated"] is False
    assert len(
        list(
            session.scalars(
                select(LiveCollectorCheckpoint).where(LiveCollectorCheckpoint.run_id == run.id)
            )
        )
    ) == len(cps)
    receipt.authorization_id = uuid4()
    with pytest.raises(PostClosePreconditionError):
        receipt.complete_once()
    session.refresh(old)
    assert old.status == "RUNNING" and old.metadata_payload == {"legacy": True}


def test_receipt_event_failure_rolls_back_run_and_never_repeats_published_home(
    completion_db, monkeypatch
):
    session, receipt, run, _, home, writes = committed_home_failed_receipt(
        completion_db, monkeypatch
    )
    before = deepcopy(run.metadata_payload)

    def fail(**_kw):
        session.flush()  # Exercise rollback AFTER an actual typed JSONB update.
        raise TypeError("controlled receipt interruption")

    monkeypatch.setattr(receipt, "_checkpoint_event", fail)
    with pytest.raises(TypeError, match="controlled receipt interruption"):
        receipt.complete_once()
    session.refresh(run)
    assert run.status == "PARTIAL" and run.metadata_payload == before
    assert not list(
        session.scalars(
            select(LiveCollectorCheckpoint).where(
                LiveCollectorCheckpoint.run_id == run.id,
                LiveCollectorCheckpoint.batch_key == RECEIPT_KEY,
            )
        )
    )
    session.refresh(home)
    assert home.publication_state == "PUBLISHED" and writes == [str(run.id)]
