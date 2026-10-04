"""One-shot Home completion persistence; disposable PostgreSQL only."""

from copy import deepcopy
from hashlib import sha256
from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from test_home_only_completion import NOW, completed_execution, market_facts

from topicpilot_api.live.config import LiveRuntimeConfig
from topicpilot_api.live.home_completion import (
    TARGET,
    OwnerHomeCompletion,
    evaluate_home_completion,
)
from topicpilot_api.live.post_close import PostClosePreconditionError
from topicpilot_api.orm import (
    HomePublication,
    LiveCollectorAttempt,
    LiveCollectorCheckpoint,
    LiveCollectorRun,
)


@pytest.fixture
def completion_db(postgres_engine, monkeypatch):
    with postgres_engine.connect() as connection:
        transaction = connection.begin()
        try:
            with Session(
                connection, expire_on_commit=False, join_transaction_mode="create_savepoint"
            ) as session:
                source, cps = completed_execution()
                run = LiveCollectorRun(
                    id=source.id,
                    run_type=source.run_type,
                    status=source.status,
                    started_at=NOW,
                    heartbeat_at=NOW,
                    completed_at=NOW,
                    provider_code="TEST_ONLY_SYNTHETIC",
                    adapter_version="test-only.v1",
                    config_hash=sha256(b"controlled test config").hexdigest(),
                    requested_count=553,
                    success_count=553,
                    failure_count=0,
                    retry_count=0,
                    failure_code=source.failure_code,
                    metadata_payload=source.metadata_payload,
                )
                old = LiveCollectorRun(
                    run_type="POST_CLOSE",
                    status="RUNNING",
                    started_at=NOW,
                    heartbeat_at=NOW,
                    provider_code="TEST_ONLY_SYNTHETIC",
                    adapter_version="test-only.v1",
                    config_hash=sha256(b"protected prior run").hexdigest(),
                    metadata_payload={"legacy": True},
                )
                session.add_all([run, old])
                session.flush()
                for number, cp in enumerate(cps):
                    session.add(
                        LiveCollectorCheckpoint(
                            **vars(cp),
                            batch_number=number,
                        )
                    )
                for symbol in ("TEST1", "TEST2"):
                    session.add(
                        LiveCollectorAttempt(
                            run_id=run.id,
                            instrument_code=symbol,
                            market_code="TPE",
                            attempt_number=1,
                            status="SUCCESS",
                            started_at=NOW,
                            updated_at=NOW,
                            provider_status="AVAILABLE",
                            freshness_state="FRESH",
                        )
                    )
                session.commit()
                completion = OwnerHomeCompletion(
                    session, LiveRuntimeConfig(), run_id=run.id, authorization_id=uuid4()
                )
                writes = []

                def preflight():
                    rows = list(
                        session.scalars(
                            select(LiveCollectorCheckpoint).where(
                                LiveCollectorCheckpoint.run_id == run.id
                            )
                        )
                    )
                    completion.expected_ids = (uuid4(),)
                    return evaluate_home_completion(session.get(LiveCollectorRun, run.id), rows)

                def materialize(
                    db,
                    *,
                    trading_date,
                    source_run_id,
                    expected_instrument_ids,
                    market_index_facts,
                    market_aggregate_facts,
                ):
                    assert db is session and trading_date == TARGET
                    assert source_run_id == str(run.id) and expected_instrument_ids
                    assert len(market_index_facts) == len(market_aggregate_facts) == 2
                    writes.append(source_run_id)
                    publication = HomePublication(
                        trading_date=trading_date,
                        generated_at=NOW,
                        published_at=NOW,
                        publication_state="PUBLISHED",
                        publication_version="test-only.v1",
                        source_run_id=source_run_id,
                        source_dataset_id=f"test-only:{uuid4()}",
                        lineage_hash=sha256(b"test home lineage").hexdigest(),
                        completeness={},
                        payload={},
                    )
                    db.add(publication)
                    db.commit()
                    return {
                        "status": "SUCCESS",
                        "publicationId": str(publication.id),
                        "publicationState": "PUBLISHED",
                    }

                def readback(*_a, **_kw):
                    published = session.scalar(
                        select(HomePublication.id).where(
                            HomePublication.source_run_id == str(run.id),
                            HomePublication.publication_state == "PUBLISHED",
                        )
                    )
                    return {
                        "status": "PASS" if published else "FAIL",
                        "topicSnapshot": {"status": "PASS"},
                        "institutionalFlow": {"status": "PASS"},
                        "homePublication": {"status": "PASS" if published else "NOT_FOUND"},
                    }

                monkeypatch.setattr(completion, "preflight", preflight)
                monkeypatch.setattr(completion, "_formal_publication_readback", readback)
                monkeypatch.setattr(
                    "topicpilot_api.live.home_completion.materialize_home_v2", materialize
                )
                yield session, completion, run, old, writes
        finally:
            transaction.rollback()


def test_home_only_success_preserves_ingestion_and_protected_previous_run(completion_db):
    session, completion, run, old, writes = completion_db
    previous_metadata = deepcopy(run.metadata_payload)
    attempts = list(
        session.scalars(select(LiveCollectorAttempt).where(LiveCollectorAttempt.run_id == run.id))
    )
    attempts_before = [(a.id, a.status, a.updated_at) for a in attempts]
    count_before = session.scalar(select(func.count()).select_from(LiveCollectorRun))
    indices, aggregates = market_facts()
    result = completion.complete_once(indices=indices, aggregates=aggregates)
    assert result["status"] == "PASS" and result["newCollectorRunCreated"] is False
    assert writes == [str(run.id)]
    assert run.status == "SUCCESS" and run.failure_code is None
    assert run.requested_count == run.success_count == 553 and run.failure_count == 0
    assert run.metadata_payload["providerPointCount"] == 552
    assert run.metadata_payload["ownerNormalExecution"] == previous_metadata["ownerNormalExecution"]
    assert run.metadata_payload["ownerNormalExecution"]["reentryAllowed"] is False
    assert (
        run.metadata_payload["statusResolutionMetrics"]
        == previous_metadata["statusResolutionMetrics"]
    )
    claim = run.metadata_payload["ownerHomeCompletion"]
    assert claim["previousState"] == "PARTIAL" and claim["previousFailureCodes"] == [
        run.metadata_payload["ownerHomeCompletion"]["previousFailureCode"]
    ]
    assert claim["status"] == "COMPLETED" and claim["providerIngestionRepeated"] is False
    assert session.scalar(select(func.count()).select_from(LiveCollectorRun)) == count_before
    session.refresh(old)
    assert old.status == "RUNNING" and old.metadata_payload == {"legacy": True}
    assert [(a.id, a.status, a.updated_at) for a in attempts] == attempts_before
    cps = list(
        session.scalars(
            select(LiveCollectorCheckpoint).where(LiveCollectorCheckpoint.run_id == run.id)
        )
    )
    assert all(
        c.provider_request_count is None and c.provider_failure_count is None
        for c in cps
        if c.batch_key == "OWNER_HOME_ONLY_COMPLETION"
    )
    assert any(c.batch_key == "FINAL_PUBLICATION" and c.status == "FAILED" for c in cps)
    assert any(c.batch_key == "FINAL_PUBLICATION" and c.status == "COMPLETED" for c in cps)
    with pytest.raises(PostClosePreconditionError):
        completion.complete_once(indices=indices, aggregates=aggregates)
    assert len(writes) == 1


@pytest.mark.parametrize("stage", ["checkpoint", "writer", "readback"])
def test_exception_after_claim_is_terminal_idempotent_and_never_zombie(
    completion_db,
    monkeypatch,
    stage,
):
    session, completion, run, old, writes = completion_db
    prior_time = run.completed_at
    if stage == "checkpoint":
        original = completion._checkpoint_event

        def interrupt(**kw):
            if kw["status"] == "IN_PROGRESS":
                raise TypeError("controlled checkpoint interruption")
            return original(**kw)

        monkeypatch.setattr(completion, "_checkpoint_event", interrupt)
    elif stage == "writer":

        def interrupt(*_a, **_kw):
            raise TypeError("controlled writer interruption")

        monkeypatch.setattr("topicpilot_api.live.home_completion.materialize_home_v2", interrupt)
    else:
        monkeypatch.setattr(
            completion, "_formal_publication_readback", lambda *_a, **_kw: {"status": "FAIL"}
        )
    indices, aggregates = market_facts()
    with pytest.raises((TypeError, PostClosePreconditionError)):
        completion.complete_once(indices=indices, aggregates=aggregates)
    session.refresh(run)
    assert run.status == "PARTIAL" and run.completed_at == prior_time
    claim = run.metadata_payload["ownerHomeCompletion"]
    assert claim["status"] == "FAILED" and claim["reentryAllowed"] is False
    assert claim["exceptionClass"] in {"TypeError", "PostClosePreconditionError"}
    assert claim["failureCode"] != "PROVIDER_INGESTION_FAILURE"
    assert claim["operatorActionRequired"] == "REVIEW_NEW_AUTHORIZATION_CONTRACT"
    before = len(writes)
    with pytest.raises(PostClosePreconditionError, match="AUTHORIZATION_ALREADY_CLAIMED"):
        completion.complete_once(indices=indices, aggregates=aggregates)
    assert len(writes) == before
    session.refresh(old)
    assert old.metadata_payload == {"legacy": True}
