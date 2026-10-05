"""Append-only daily formal publication receipts and operator readback.

The receipt is a semantic projection of the existing post-close run,
checkpoint, reconciliation, publication, and runtime authorities.  It does
not replace any of them and it is never updated in place.
"""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from datetime import UTC, date, datetime, time
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import func, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from topicpilot_api.normalizer.contracts import stable_hash
from topicpilot_api.orm import DailyFormalPublicationReceipt, LiveCollectorRun
from topicpilot_api.release_provenance import runtime_git_sha

from .config import LiveRuntimeConfig

RECEIPT_COMPLETE = "COMPLETE"
RECEIPT_MARKET_CLOSED = "MARKET_CLOSED"
RECEIPT_WAITING_FOR_DATA = "WAITING_FOR_DATA"
RECEIPT_FAILED_CLOSED = "FAILED_CLOSED"
RECEIPT_DEADLINE_EXCEEDED = "DEADLINE_EXCEEDED"
RECEIPT_CORRECTION_COMPLETE = "CORRECTION_COMPLETE"
RECEIPT_CORRECTION_FAILED = "CORRECTION_FAILED"
RUNTIME_PROVENANCE_TRUST_FAILURE = "RUNTIME_PROVENANCE_TRUST_FAILURE"

_SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$", re.IGNORECASE)


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    return value


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("receipt clock must be timezone-aware")
    return value.astimezone(UTC)


def _local_boundary(trading_date: date, value: str, timezone_name: str) -> datetime:
    return datetime.combine(
        trading_date,
        time.fromisoformat(value),
        tzinfo=ZoneInfo(timezone_name),
    ).astimezone(UTC)


def soft_target_at(trading_date: date, config: LiveRuntimeConfig) -> datetime:
    return _local_boundary(trading_date, config.soft_target, config.timezone_name)


def hard_deadline_at(trading_date: date, config: LiveRuntimeConfig) -> datetime:
    return _local_boundary(trading_date, config.hard_deadline, config.timezone_name)


def operational_phase(
    now: datetime,
    trading_date: date,
    config: LiveRuntimeConfig,
    *,
    data_ready: bool,
    market_closed: bool = False,
) -> str:
    """Resolve the clock-owned phase without asserting business readiness."""

    if market_closed:
        return RECEIPT_MARKET_CLOSED
    current = _as_utc(now)
    if data_ready:
        return "DATA_READY"
    if current >= hard_deadline_at(trading_date, config):
        return RECEIPT_DEADLINE_EXCEEDED
    if current >= soft_target_at(trading_date, config):
        return "SOFT_TARGET_NOT_READY"
    return RECEIPT_WAITING_FOR_DATA


def _validated_sha(value: str | None) -> tuple[str, str]:
    if value and _SHA_PATTERN.fullmatch(value.strip()):
        return value.strip().lower(), "READY"
    return "UNKNOWN", "UNVERIFIED"


def runtime_provenance(session: Session) -> dict[str, Any]:
    """Read current-process/runtime markers without claiming unavailable proof."""

    worker_sha, worker_status = _validated_sha(runtime_git_sha())
    api_sha, api_status = _validated_sha(os.getenv("TOPICPILOT_API_RUNTIME_SHA"))
    web_sha, web_status = _validated_sha(os.getenv("TOPICPILOT_WEB_ARTIFACT_SHA"))
    try:
        migration_head = session.execute(
            text(
                "SELECT version_num FROM public.alembic_version "
                "ORDER BY version_num LIMIT 1"
            )
        ).scalar_one_or_none()
    except Exception:
        migration_head = None
    migration_status = "READY" if migration_head else "UNVERIFIED"
    known_required = (
        worker_status == "READY"
        and api_status == "READY"
        and migration_status == "READY"
    )
    return {
        "status": "READY" if known_required else "DEGRADED",
        "worker": {
            "runtimeGitSha": worker_sha,
            "readbackStatus": worker_status,
            "source": "RENDER_GIT_COMMIT_OR_GIT_SHA",
        },
        "api": {
            "runtimeGitSha": api_sha,
            "readbackStatus": api_status,
            "source": "TOPICPILOT_API_RUNTIME_SHA",
        },
        "migration": {
            "head": migration_head or "UNKNOWN",
            "readbackStatus": migration_status,
            "source": "public.alembic_version",
        },
        "web": {
            "artifactSha": web_sha,
            "readbackStatus": web_status,
            "source": "TOPICPILOT_WEB_ARTIFACT_SHA",
        },
        "unknownIsVerified": False,
        "blocking": False,
    }


def runtime_provenance_event(
    provenance: Mapping[str, Any], now: datetime
) -> dict[str, Any] | None:
    """Return an actionable event when required runtime proof is incomplete."""

    # Web provenance is required when a Web artifact participates in the
    # release. Worker receipts always require independent Worker, API, and
    # migration proof for the live publication path.
    required_components = ("worker", "api", "migration")
    unverified = [
        component
        for component in required_components
        if (provenance.get(component) or {}).get("readbackStatus") != "READY"
    ]
    if not unverified:
        return None
    return {
        "code": RUNTIME_PROVENANCE_TRUST_FAILURE,
        "severity": "CRITICAL",
        "actionRequired": True,
        "at": _as_utc(now).isoformat(),
        "unverifiedComponents": unverified,
    }


def _state(value: Any, *, default: str = "NOT_RUN") -> str:
    if isinstance(value, Mapping):
        status = value.get("status") or value.get("publicationStatus")
    else:
        status = value
    if status in {"PASS", "SUCCESS", "PUBLISHED", "COMPLETE"}:
        return "PUBLISHED"
    if status in {"FORBIDDEN", "NOT_APPLICABLE"}:
        return str(status)
    if status in {"NOT_RUN", None}:
        return default
    return str(status)


def _failure_stage(metadata: Mapping[str, Any]) -> str | None:
    codes = metadata.get("failureCodes") or []
    if codes:
        return str(codes[0])
    readback = (metadata.get("topicSnapshot") or {}).get("formalPublicationReadback") or {}
    for key in (
        "topicSnapshot",
        "institutionalFlow",
        "formalStrength",
        "formalLifecycle",
        "homePublication",
    ):
        section = readback.get(key) or {}
        if section.get("status") not in {None, "PASS", "NOT_CHECKED", "FORBIDDEN"}:
            return key
    return None


def _reason_code(metadata: Mapping[str, Any], receipt_status: str) -> str | None:
    if receipt_status == RECEIPT_DEADLINE_EXCEEDED:
        return "HARD_DEADLINE_EXCEEDED"
    if receipt_status == RECEIPT_WAITING_FOR_DATA:
        return "DATA_NOT_READY"
    codes = metadata.get("failureCodes") or []
    return str(codes[0]) if codes else None


def read_latest_receipt(
    session: Session, trading_date: date
) -> DailyFormalPublicationReceipt | None:
    """Read the latest immutable receipt for one trading date."""

    try:
        return session.scalar(
            select(DailyFormalPublicationReceipt)
            .where(DailyFormalPublicationReceipt.trading_date == trading_date)
            .order_by(
                DailyFormalPublicationReceipt.created_at.desc(),
                DailyFormalPublicationReceipt.receipt_revision.desc(),
                DailyFormalPublicationReceipt.id.desc(),
            )
            .limit(1)
        )
    except Exception:
        rollback = getattr(session, "rollback", None)
        if callable(rollback):
            rollback()
        return None


def read_receipts(
    session: Session, trading_date: date, *, limit: int = 50
) -> list[DailyFormalPublicationReceipt]:
    """Read immutable receipt history in newest-first order."""
    bounded_limit = max(1, min(int(limit), 200))
    try:
        return list(
            session.scalars(
                select(DailyFormalPublicationReceipt)
                .where(DailyFormalPublicationReceipt.trading_date == trading_date)
                .order_by(
                    DailyFormalPublicationReceipt.created_at.desc(),
                    DailyFormalPublicationReceipt.receipt_revision.desc(),
                    DailyFormalPublicationReceipt.id.desc(),
                )
                .limit(bounded_limit)
            )
        )
    except Exception:
        rollback = getattr(session, "rollback", None)
        if callable(rollback):
            rollback()
        return []


def _previous_authority(
    session: Session,
    trading_date: date,
    execution_key: str,
) -> DailyFormalPublicationReceipt | None:
    try:
        return session.scalar(
            select(DailyFormalPublicationReceipt)
            .where(
                DailyFormalPublicationReceipt.trading_date == trading_date,
                DailyFormalPublicationReceipt.execution_key != execution_key,
                DailyFormalPublicationReceipt.receipt_status.in_(
                    (RECEIPT_COMPLETE, RECEIPT_CORRECTION_COMPLETE)
                ),
            )
            .order_by(
                DailyFormalPublicationReceipt.created_at.desc(),
                DailyFormalPublicationReceipt.receipt_revision.desc(),
            )
            .limit(1)
        )
    except SQLAlchemyError:
        session.rollback()
        return None


def _receipt_status(
    run_status: str,
    metadata: Mapping[str, Any],
    execution_scope: str,
    now: datetime,
    trading_date: date,
    config: LiveRuntimeConfig,
) -> str:
    reconciliation = metadata.get("dailyMarketReconciliation") or {}
    snapshot = metadata.get("topicSnapshot") or {}
    readback = snapshot.get("formalPublicationReadback") or {}
    market_closed = run_status == "MARKET_CLOSED" or reconciliation.get("status") == "MARKET_CLOSED"
    if market_closed:
        return RECEIPT_MARKET_CLOSED
    formal_ready = readback.get("status") == "PASS"
    data_ready = reconciliation.get("downstreamReady") is True
    if run_status == "SUCCESS" and data_ready and formal_ready:
        return (
            RECEIPT_CORRECTION_COMPLETE
            if execution_scope == "HISTORY_RECOVERY"
            else RECEIPT_COMPLETE
        )
    if _as_utc(now) >= hard_deadline_at(trading_date, config) and not data_ready:
        return RECEIPT_DEADLINE_EXCEEDED
    if not data_ready:
        return RECEIPT_WAITING_FOR_DATA
    return (
        RECEIPT_CORRECTION_FAILED
        if execution_scope == "HISTORY_RECOVERY"
        else RECEIPT_FAILED_CLOSED
    )


def _summary_payload(metadata: Mapping[str, Any]) -> dict[str, Any]:
    snapshot = metadata.get("topicSnapshot") or {}
    return _json_safe(
        {
            "failureCodes": metadata.get("failureCodes") or [],
            "downstreamReady": metadata.get("downstreamReady"),
            "dailyMarketReconciliation": metadata.get("dailyMarketReconciliation") or {},
            "statusResolutionMetrics": metadata.get("statusResolutionMetrics") or {},
            "topicSnapshot": {
                key: snapshot.get(key)
                for key in (
                    "snapshotDate",
                    "topicCount",
                    "status",
                    "formalTopicDailyState",
                    "formalTopicSnapshotReadback",
                    "formalStrength",
                    "formalStrengthReadback",
                    "formalLifecycle",
                    "formalLifecycleReadback",
                    "homePublication",
                    "formalPublicationReadback",
                )
                if key in snapshot
            },
            "forwardAutomation": metadata.get("forwardAutomation") or {},
            "historyRecovery": metadata.get("historyRecovery") or {},
        }
    )


def append_receipt_for_run(
    session: Session,
    run: LiveCollectorRun,
    config: LiveRuntimeConfig,
    *,
    now: datetime | None = None,
    commit: bool = False,
) -> DailyFormalPublicationReceipt:
    """Append one idempotent receipt observation for a terminal/run state."""

    metadata = dict(run.metadata_payload or {})
    run_date_value = metadata.get("runDate") or metadata.get("targetDate")
    if not run_date_value:
        raise ValueError("daily receipt requires a run date")
    trading_date = date.fromisoformat(str(run_date_value))
    current = _as_utc(now or datetime.now(UTC))
    execution_key = str(metadata.get("executionKey") or f"post-close:{trading_date.isoformat()}")
    execution_scope = str(metadata.get("executionScope") or "NORMAL_CURRENT_DAY")
    status = _receipt_status(
        run.status,
        metadata,
        execution_scope,
        current,
        trading_date,
        config,
    )
    reconciliation = metadata.get("dailyMarketReconciliation") or {}
    snapshot = metadata.get("topicSnapshot") or {}
    readback = snapshot.get("formalPublicationReadback") or {}
    data_ready = reconciliation.get("downstreamReady") is True
    phase = operational_phase(
        current,
        trading_date,
        config,
        data_ready=data_ready,
        market_closed=status == RECEIPT_MARKET_CLOSED,
    )
    events: list[dict[str, Any]] = []
    if not data_ready and current >= soft_target_at(trading_date, config):
        events.append(
            {
                "code": "SOFT_TARGET_NOT_READY",
                "severity": "WARNING",
                "at": current.isoformat(),
            }
        )
    if status == RECEIPT_DEADLINE_EXCEEDED:
        events.append(
            {
                "code": "HARD_DEADLINE_EXCEEDED",
                "severity": "CRITICAL",
                "at": current.isoformat(),
            }
        )
    if status in {RECEIPT_FAILED_CLOSED, RECEIPT_CORRECTION_FAILED}:
        events.append(
            {
                "code": "FORMAL_INTEGRITY_FAILURE",
                "severity": "CRITICAL",
                "at": current.isoformat(),
            }
        )
    runtime = runtime_provenance(session)
    runtime_event = runtime_provenance_event(runtime, current)
    if runtime_event is not None:
        events.append(runtime_event)
    correction = execution_scope == "HISTORY_RECOVERY"
    previous = _previous_authority(session, trading_date, execution_key) if correction else None
    correction_lineage = {
        "kind": "HISTORY_RECOVERY" if correction else "NORMAL_DAILY_PUBLICATION",
        "replayRequired": correction,
        "replayStartDate": trading_date.isoformat() if correction else None,
        "replayEndDate": trading_date.isoformat() if correction else None,
        "supersedesReceiptId": str(previous.id) if previous is not None else None,
    }
    formal_identifiers = _json_safe(
        {
            "topicSnapshot": snapshot.get("formalTopicSnapshotReadback") or {},
            "strength": snapshot.get("formalStrength") or {},
            "lifecycle": snapshot.get("formalLifecycle") or {},
            "formalReadback": readback,
        }
    )
    payload = _summary_payload(metadata)
    hash_material = _json_safe(
        {
            "tradingDate": trading_date,
            "executionKey": execution_key,
            "executionScope": execution_scope,
            "runStatus": run.status,
            "receiptStatus": status,
            "postCloseState": phase,
            "reconciliation": reconciliation,
            "formalIdentifiers": formal_identifiers,
            "reasonCode": _reason_code(metadata, status),
            "correctionLineage": correction_lineage,
        }
    )
    receipt_hash = stable_hash(hash_material)
    existing = session.scalar(
        select(DailyFormalPublicationReceipt).where(
            DailyFormalPublicationReceipt.execution_key == execution_key,
            DailyFormalPublicationReceipt.receipt_hash == receipt_hash,
        )
    )
    if existing is not None:
        return existing
    revision = (
        session.scalar(
            select(func.max(DailyFormalPublicationReceipt.receipt_revision)).where(
                DailyFormalPublicationReceipt.execution_key == execution_key
            )
        )
        or 0
    ) + 1
    generation = int(metadata.get("resumeCount", 0) or 0) + 1
    readiness_at = metadata.get("dataReadyAt")
    publication_at = metadata.get("formalPublicationAt")
    receipt = DailyFormalPublicationReceipt(
        trading_date=trading_date,
        calendar_code=config.calendar_code,
        reference_data_version=config.reference_data_version,
        calendar_decision={
            "authority": "G2_REFERENCE_CALENDAR",
            "calendarCode": config.calendar_code,
            "referenceDataVersion": config.reference_data_version,
            "targetDate": trading_date.isoformat(),
            "targetDateIsSession": reconciliation.get("status") != "MARKET_CLOSED",
            "reasonCode": reconciliation.get("reasonCodes", [None])[0]
            if reconciliation.get("reasonCodes")
            else None,
        },
        execution_key=execution_key,
        execution_scope=execution_scope,
        execution_generation=generation,
        receipt_revision=revision,
        source_run_id=run.id,
        source_run_status=run.status,
        started_at=run.started_at,
        readiness_at=(datetime.fromisoformat(readiness_at) if readiness_at else None),
        publication_at=(datetime.fromisoformat(publication_at) if publication_at else None),
        completed_at=run.completed_at or current,
        post_close_state=phase,
        reconciliation_state=str(reconciliation.get("status") or "NOT_RUN"),
        absolute_strength_state=_state(
            (snapshot.get("formalStrengthReadback") or snapshot.get("formalStrength")),
            default="WAITING_FOR_FORMAL_SNAPSHOT",
        ),
        relative_strength_state=_state(
            (snapshot.get("formalStrengthReadback") or snapshot.get("formalStrength")),
            default="WAITING_FOR_FORMAL_SNAPSHOT",
        ),
        formal_grade_state=_state(
            (snapshot.get("formalStrengthReadback") or snapshot.get("formalStrength")),
            default="WAITING_FOR_FORMAL_SNAPSHOT",
        ),
        lifecycle_state=_state(
            snapshot.get("formalLifecycleReadback") or snapshot.get("formalLifecycle"),
            default="WAITING_FOR_FORMAL_SNAPSHOT",
        ),
        home_state=_state(snapshot.get("homePublication"), default="NOT_RUN"),
        formal_readback_state=str(readback.get("status") or "NOT_RUN"),
        receipt_status=status,
        failure_stage=_failure_stage(metadata),
        reason_code=_reason_code(metadata, status),
        receipt_hash=receipt_hash,
        runtime_provenance=runtime,
        formal_identifiers=formal_identifiers,
        correction_lineage=correction_lineage,
        supersedes_receipt_id=previous.id if previous is not None else None,
        operational_events=events,
        payload=payload,
    )
    session.add(receipt)
    if commit:
        session.commit()
    return receipt


def append_correction_receipt(
    session: Session,
    *,
    config: LiveRuntimeConfig,
    trading_date: date,
    earliest_affected_date: date,
    replay_end_date: date,
    execution_key: str,
    replay_result: Mapping[str, Any],
    reason_code: str,
    now: datetime,
    supersedes_receipt_id: UUID | None = None,
    commit: bool = False,
) -> DailyFormalPublicationReceipt:
    """Append a correction receipt for a bounded path-dependent replay.

    Correction never mutates the prior daily authority.  The new receipt
    points at the superseded authority and records the exact replay range.
    """
    current = _as_utc(now)
    status = (
        RECEIPT_CORRECTION_COMPLETE
        if str(replay_result.get("status")) == "SUCCESS"
        else RECEIPT_CORRECTION_FAILED
    )
    previous = _previous_authority(session, trading_date, execution_key)
    supersedes = supersedes_receipt_id or (previous.id if previous is not None else None)
    lineage = {
        "kind": "HISTORY_RECOVERY",
        "replayRequired": True,
        "earliestAffectedDate": earliest_affected_date.isoformat(),
        "replayStartDate": earliest_affected_date.isoformat(),
        "replayEndDate": replay_end_date.isoformat(),
        "supersedesReceiptId": str(supersedes) if supersedes is not None else None,
        "homeReplayed": False,
    }
    payload = _json_safe(
        {
            "reasonCode": reason_code,
            "replay": replay_result,
            "authority": "FORMAL_LIFECYCLE_REPLAY",
        }
    )
    receipt_hash = stable_hash(
        _json_safe(
            {
                "tradingDate": trading_date,
                "executionKey": execution_key,
                "receiptStatus": status,
                "reasonCode": reason_code,
                "lineage": lineage,
                "replay": replay_result,
            }
        )
    )
    existing = session.scalar(
        select(DailyFormalPublicationReceipt).where(
            DailyFormalPublicationReceipt.execution_key == execution_key,
            DailyFormalPublicationReceipt.receipt_hash == receipt_hash,
        )
    )
    if existing is not None:
        return existing
    revision = (
        session.scalar(
            select(func.max(DailyFormalPublicationReceipt.receipt_revision)).where(
                DailyFormalPublicationReceipt.execution_key == execution_key
            )
        )
        or 0
    ) + 1
    event_code = (
        "CORRECTION_REPLAY_COMPLETE"
        if status == RECEIPT_CORRECTION_COMPLETE
        else "CORRECTION_REPLAY_FAILED"
    )
    runtime = runtime_provenance(session)
    events = [
        {
            "code": event_code,
            "severity": "INFO" if status == RECEIPT_CORRECTION_COMPLETE else "CRITICAL",
            "at": current.isoformat(),
        }
    ]
    runtime_event = runtime_provenance_event(runtime, current)
    if runtime_event is not None:
        events.append(runtime_event)
    receipt = DailyFormalPublicationReceipt(
        trading_date=trading_date,
        calendar_code=config.calendar_code,
        reference_data_version=config.reference_data_version,
        calendar_decision={
            "authority": "G2_REFERENCE_CALENDAR",
            "calendarCode": config.calendar_code,
            "referenceDataVersion": config.reference_data_version,
            "targetDate": trading_date.isoformat(),
        },
        execution_key=execution_key,
        execution_scope="CORRECTION_REPLAY",
        execution_generation=1,
        receipt_revision=revision,
        source_run_id=None,
        source_run_status=None,
        started_at=None,
        readiness_at=current if status == RECEIPT_CORRECTION_COMPLETE else None,
        publication_at=current if status == RECEIPT_CORRECTION_COMPLETE else None,
        completed_at=current,
        post_close_state="CORRECTION_REPLAY",
        reconciliation_state="NOT_RUN",
        absolute_strength_state="NOT_RUN",
        relative_strength_state="NOT_RUN",
        formal_grade_state="NOT_RUN",
        lifecycle_state=("PUBLISHED" if status == RECEIPT_CORRECTION_COMPLETE else "FAILED"),
        home_state="FORBIDDEN",
        formal_readback_state=("PASS" if status == RECEIPT_CORRECTION_COMPLETE else "FAIL"),
        receipt_status=status,
        failure_stage=None if status == RECEIPT_CORRECTION_COMPLETE else "CORRECTION_REPLAY",
        reason_code=reason_code,
        receipt_hash=receipt_hash,
        runtime_provenance=runtime,
        formal_identifiers={
            "lifecycleContractVersion": replay_result.get("contractVersion"),
            "calculationVersion": replay_result.get("calculationVersion"),
        },
        correction_lineage=lineage,
        supersedes_receipt_id=supersedes,
        operational_events=events,
        payload=payload,
    )
    session.add(receipt)
    if commit:
        session.commit()
    return receipt


def append_operational_receipt(
    session: Session,
    *,
    trading_date: date,
    config: LiveRuntimeConfig,
    execution_key: str,
    receipt_status: str,
    reason_code: str,
    now: datetime,
    calendar_decision: Mapping[str, Any] | None = None,
    commit: bool = True,
) -> DailyFormalPublicationReceipt:
    """Append a scheduler-owned terminal/warning observation without a run."""

    current = _as_utc(now)
    event = {
        "code": reason_code,
        "severity": "CRITICAL" if receipt_status == RECEIPT_DEADLINE_EXCEEDED else "WARNING",
        "at": current.isoformat(),
    }
    runtime = runtime_provenance(session)
    runtime_event = runtime_provenance_event(runtime, current)
    events = [event]
    if runtime_event is not None:
        events.append(runtime_event)
    payload = {
        "schedulerAuthority": "WAKEUP_ONLY",
        "reasonCode": reason_code,
        "hardDeadline": hard_deadline_at(trading_date, config).isoformat(),
    }
    receipt_hash = stable_hash(
        {
            "tradingDate": trading_date,
            "executionKey": execution_key,
            "receiptStatus": receipt_status,
            "reasonCode": reason_code,
        }
    )
    existing = session.scalar(
        select(DailyFormalPublicationReceipt).where(
            DailyFormalPublicationReceipt.execution_key == execution_key,
            DailyFormalPublicationReceipt.receipt_hash == receipt_hash,
        )
    )
    if existing is not None:
        return existing
    revision = (
        session.scalar(
            select(func.max(DailyFormalPublicationReceipt.receipt_revision)).where(
                DailyFormalPublicationReceipt.execution_key == execution_key
            )
        )
        or 0
    ) + 1
    receipt = DailyFormalPublicationReceipt(
        trading_date=trading_date,
        calendar_code=config.calendar_code,
        reference_data_version=config.reference_data_version,
        calendar_decision=_json_safe(calendar_decision or {"authority": "G2_REFERENCE_CALENDAR"}),
        execution_key=execution_key,
        execution_scope="SCHEDULER",
        execution_generation=1,
        receipt_revision=revision,
        source_run_id=None,
        source_run_status=None,
        started_at=None,
        readiness_at=None,
        publication_at=None,
        completed_at=current,
        post_close_state=receipt_status,
        reconciliation_state="NOT_RUN",
        absolute_strength_state="NOT_RUN",
        relative_strength_state="NOT_RUN",
        formal_grade_state="NOT_RUN",
        lifecycle_state="NOT_RUN",
        home_state="NOT_RUN",
        formal_readback_state="NOT_RUN",
        receipt_status=receipt_status,
        failure_stage="SCHEDULER",
        reason_code=reason_code,
        receipt_hash=receipt_hash,
        runtime_provenance=runtime,
        formal_identifiers={},
        correction_lineage={"kind": "NORMAL_DAILY_PUBLICATION", "replayRequired": False},
        supersedes_receipt_id=None,
        operational_events=events,
        payload=payload,
    )
    session.add(receipt)
    if commit:
        session.commit()
    return receipt


def receipt_to_dict(receipt: DailyFormalPublicationReceipt) -> dict[str, Any]:
    return _json_safe(
        {
            "receiptId": receipt.id,
            "tradingDate": receipt.trading_date,
            "calendarCode": receipt.calendar_code,
            "referenceDataVersion": receipt.reference_data_version,
            "calendarDecision": receipt.calendar_decision,
            "executionKey": receipt.execution_key,
            "executionScope": receipt.execution_scope,
            "executionGeneration": receipt.execution_generation,
            "receiptRevision": receipt.receipt_revision,
            "sourceRunId": receipt.source_run_id,
            "sourceRunStatus": receipt.source_run_status,
            "startedAt": receipt.started_at,
            "readinessAt": receipt.readiness_at,
            "publicationAt": receipt.publication_at,
            "completedAt": receipt.completed_at,
            "postCloseState": receipt.post_close_state,
            "reconciliationState": receipt.reconciliation_state,
            "absoluteStrengthState": receipt.absolute_strength_state,
            "relativeStrengthState": receipt.relative_strength_state,
            "formalGradeState": receipt.formal_grade_state,
            "lifecycleState": receipt.lifecycle_state,
            "homeState": receipt.home_state,
            "formalReadbackState": receipt.formal_readback_state,
            "receiptStatus": receipt.receipt_status,
            "failureStage": receipt.failure_stage,
            "reasonCode": receipt.reason_code,
            "receiptHash": receipt.receipt_hash,
            "runtimeProvenance": receipt.runtime_provenance,
            "formalIdentifiers": receipt.formal_identifiers,
            "correctionLineage": receipt.correction_lineage,
            "supersedesReceiptId": receipt.supersedes_receipt_id,
            "operationalEvents": receipt.operational_events,
            "payload": receipt.payload,
            "createdAt": receipt.created_at,
        }
    )


__all__ = [
    "RECEIPT_COMPLETE",
    "RECEIPT_CORRECTION_COMPLETE",
    "RECEIPT_CORRECTION_FAILED",
    "RECEIPT_DEADLINE_EXCEEDED",
    "RECEIPT_FAILED_CLOSED",
    "RECEIPT_MARKET_CLOSED",
    "RECEIPT_WAITING_FOR_DATA",
    "RUNTIME_PROVENANCE_TRUST_FAILURE",
    "append_correction_receipt",
    "append_operational_receipt",
    "append_receipt_for_run",
    "hard_deadline_at",
    "operational_phase",
    "read_latest_receipt",
    "read_receipts",
    "receipt_to_dict",
    "runtime_provenance",
    "runtime_provenance_event",
    "soft_target_at",
]
