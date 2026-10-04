"""Fresh normal claims and terminal closure against the disposable test DB."""

from datetime import UTC, datetime
from hashlib import sha256
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from test_final_publication_contract import TARGET

from topicpilot_api.live.config import LiveRuntimeConfig
from topicpilot_api.live.normal_execution import OwnerNormalExecution
from topicpilot_api.live.post_close import PostClosePreconditionError
from topicpilot_api.orm import LiveCollectorCheckpoint, LiveCollectorRun


@pytest.fixture
def normal_claim_fixture(postgres_engine):
    with postgres_engine.connect() as connection:
        transaction = connection.begin()
        try:
            with Session(
                connection, expire_on_commit=False, join_transaction_mode="create_savepoint"
            ) as session:
                now = datetime(2026, 10, 4, tzinfo=UTC)
                config = LiveRuntimeConfig(reference_data_version=f"normal-{uuid4().hex}")
                old = LiveCollectorRun(
                    run_type="POST_CLOSE",
                    status="PARTIAL",
                    provider_code="OFFICIAL_DAILY_ROUTER",
                    adapter_version="official-daily-router.v1",
                    config_hash=sha256(b"test config").hexdigest(),
                    started_at=now,
                    heartbeat_at=now,
                    completed_at=now,
                    metadata_payload={
                        "runDate": TARGET.isoformat(),
                        "scope": "FULL",
                        "executionMode": "SCHEDULED",
                        "executionKey": (
                            f"post-close:{config.reference_data_version}:TW_MARKET:{TARGET}:FULL"
                        ),
                    },
                )
                session.add(old)
                session.flush()
                session.add(
                    LiveCollectorCheckpoint(
                        run_id=old.id,
                        batch_number=1000,
                        batch_key="COMPLETION",
                        attempt_number=1,
                        status="PARTIAL",
                        checkpoint_hash=sha256(b"completion").hexdigest(),
                        metadata_payload={},
                    )
                )
                session.commit()
                updater = OwnerNormalExecution(
                    session, config, execution_id=uuid4(), supersedes_run_id=old.id
                )
                yield session, updater, old, now
        finally:
            transaction.rollback()


def claim(updater, now):
    return updater._prepare_run(
        run_date=TARGET,
        now=now,
        requested_count=553,
        target_symbols=(),
        is_targeted=False,
        allow_terminal_recovery=False,
        execution_mode="MANUAL",
        context=SimpleNamespace(target_date_is_session=True),
    )


def test_fresh_claim_exception_closes_once_and_never_changes_previous_run(
    normal_claim_fixture, monkeypatch
):
    session, updater, old, now = normal_claim_fixture
    previous = dict(old.metadata_payload)
    claimed = []

    def interrupt(**kwargs):
        run, reused, totals = claim(updater, now)
        assert not reused and totals == {} and run.id != old.id
        assert run.metadata_payload["executionScope"] == "NORMAL_CURRENT_DAY"
        assert run.metadata_payload["ownerNormalExecution"]["reentryAllowed"] is False
        claimed.append(run.id)
        raise TypeError("controlled test interruption after fresh claim")

    monkeypatch.setattr(updater, "_run_once", interrupt)
    with pytest.raises(TypeError, match="controlled test interruption"):
        updater.run_once(run_date=TARGET)
    run = session.get(LiveCollectorRun, claimed[0])
    assert run.status == "FAILED" and run.completed_at is not None
    assert run.metadata_payload["orchestrationFailure"]["exceptionClass"] == "TypeError"
    assert run.metadata_payload["orchestrationFailure"]["resumeCount"] == 0
    assert run.metadata_payload["reentryContract"]["eligible"] is False
    completed_at = run.completed_at
    updater._close_orchestration_failure(run.id, TypeError("repeat test closure"))
    assert run.completed_at == completed_at
    session.refresh(old)
    assert old.status == "PARTIAL" and old.metadata_payload == previous
    assert old.completed_at == now and old.heartbeat_at == now
    successor = OwnerNormalExecution(
        session, updater.config, execution_id=uuid4(), supersedes_run_id=old.id
    )
    with pytest.raises(PostClosePreconditionError, match="AUTHORIZATION_ALREADY_CLAIMED"):
        claim(successor, now)
    assert (
        session.scalar(
            select(func.count())
            .select_from(LiveCollectorRun)
            .where(
                LiveCollectorRun.metadata_payload["runDate"].as_string() == TARGET.isoformat(),
                LiveCollectorRun.status == "RUNNING",
            )
        )
        == 0
    )


def test_missing_completion_blocks_before_any_fresh_run_write(normal_claim_fixture):
    session, updater, old, now = normal_claim_fixture
    completion = session.scalar(
        select(LiveCollectorCheckpoint).where(LiveCollectorCheckpoint.run_id == old.id)
    )
    completion.attempt_number = 2
    session.commit()
    before = session.scalar(select(func.count()).select_from(LiveCollectorRun))
    with pytest.raises(PostClosePreconditionError, match="CHECKPOINT_CONTINUITY_INVALID"):
        claim(updater, now)
    assert session.scalar(select(func.count()).select_from(LiveCollectorRun)) == before
    assert old.status == "PARTIAL"
