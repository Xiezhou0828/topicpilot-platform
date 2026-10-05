"""Official daily-data post-close runner for full or targeted instruments."""

from __future__ import annotations

import time
from collections.abc import Callable, Collection, Mapping
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from datetime import time as clock_time
from decimal import Decimal
from typing import Any
from urllib.request import Request, urlopen
from uuid import NAMESPACE_URL, UUID, uuid5
from zoneinfo import ZoneInfo

from sqlalchemy import and_, or_, select, text
from sqlalchemy.exc import DBAPIError, IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from topicpilot_api.daily_market import DailyMarketReconciliation, reconcile_daily_market
from topicpilot_api.formal_strength_publication import FormalStrengthPublisher
from topicpilot_api.home_v2_publication import materialize_home_v2
from topicpilot_api.instrument_universe import (
    INELIGIBLE_LIFECYCLE_STATUSES,
    evaluate_instrument_eligibility,
    resolve_lifecycle_status,
)
from topicpilot_api.lifecycle_formal_publication import FormalLifecyclePublisher
from topicpilot_api.market_data.aggregate_contract import fetch_official_market_aggregates
from topicpilot_api.market_data.availability import LEGITIMATE_UNAVAILABLE_CODES
from topicpilot_api.market_data.index_contract import fetch_official_market_indexes
from topicpilot_api.market_data.ingestion import (
    HistoricalInstrumentResult,
    HistoricalSourceRegistration,
    ingest_historical,
)
from topicpilot_api.market_data.institutional_flow_contract import (
    fetch_official_market_institutional_flows,
    persist_market_institutional_flows,
)
from topicpilot_api.market_data.rate_limit import RateLimitedTransport
from topicpilot_api.market_data.registry import build_historical_provider_registry
from topicpilot_api.normalizer import HISTORICAL_MAPPING_POLICY_VERSION, MappingPolicy
from topicpilot_api.normalizer.contracts import stable_hash
from topicpilot_api.orm import (
    HomePublication,
    Instrument,
    LiveCollectorAttempt,
    LiveCollectorCheckpoint,
    LiveCollectorRun,
    Market,
    TopicSnapshot,
)
from topicpilot_api.provider_preflight import load_g2_preflight_context
from topicpilot_api.topic_daily_state import materialize_bounded_formal_dates
from topicpilot_api.topic_snapshot_engine import TopicSnapshotEngine
from topicpilot_api.trading_status_authority import (
    StatusResolutionMetrics,
    TradingStatusAuthorityError,
    TradingStatusResolution,
    read_effective_trading_status_authority,
    resolve_missing_statuses_with_budget,
)

from .checkpoint_contract import checkpoint_stable_hash
from .config import LiveRuntimeConfig
from .persistence import LiveRepository
from .receipt import append_receipt_for_run
from .session import MarketSessionClock

POST_CLOSE_PHASE_MODEL = (
    "SESSION_VALIDATION",
    "INPUT_READINESS",
    "FORMAL_MARKET_FACTS",
    "A9_B2_FORMAL_PROCESSING",
    "FINAL_PUBLICATION",
    "COMPLETION",
)
NORMAL_CURRENT_DAY = "NORMAL_CURRENT_DAY"
HISTORY_RECOVERY = "HISTORY_RECOVERY"
_CHECKPOINT_BATCH_NUMBERS = {
    "SESSION_VALIDATION": 0,
    "INPUT_READINESS": 1,
    "A9_B2_FORMAL_PROCESSING": 2,
    "FINAL_PUBLICATION": 3,
    "COMPLETION": 4,
}


def _execution_scope(execution_mode: str) -> str:
    if execution_mode == "RECOVERY":
        return HISTORY_RECOVERY
    if execution_mode in {"SCHEDULED", "MANUAL"}:
        return NORMAL_CURRENT_DAY
    raise ValueError("invalid POST_CLOSE execution_mode")


def _metadata_execution_scope(metadata: Mapping[str, Any]) -> str:
    recorded = metadata.get("executionScope")
    if recorded in {NORMAL_CURRENT_DAY, HISTORY_RECOVERY}:
        return str(recorded)
    if metadata.get("executionMode") == "RECOVERY" or metadata.get("recoveryOfRunId"):
        return HISTORY_RECOVERY
    return NORMAL_CURRENT_DAY


def _official_transport(url: str, timeout: float) -> bytes:
    request = Request(url, headers={"User-Agent": "TopicPilot-V2/1.0"})
    with urlopen(request, timeout=timeout) as response:
        return response.read()


def _json_safe(value: Any) -> Any:
    """Convert finalization metadata into values accepted by JSONB."""

    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, (Decimal, UUID)):
        return str(value)
    return value


def _checkpoint_semantics(batch_key: str) -> str:
    if batch_key.startswith("FORMAL_MARKET_FACTS:"):
        parts = batch_key.split(":")
        if len(parts) >= 3 and parts[1] in {"TPE", "TWO"}:
            return "PROVIDER_INGESTION"
        if batch_key == "FORMAL_MARKET_FACTS:OFFICIAL":
            return "INSTITUTIONAL_FLOW_PUBLICATION_READBACK"
    return {
        "STATUS_RESOLUTION": "TRADING_STATUS_AUTHORITY_RESOLUTION",
        "A9_B2_FORMAL_PROCESSING": "FORMAL_MARKET_FACTS_PERSISTENCE",
        "FINAL_PUBLICATION": "FINAL_FORMAL_PUBLICATION",
        "COMPLETION": "RUN_COMPLETION",
    }.get(batch_key, "POST_CLOSE_ORCHESTRATION")


def _provider_metrics_applicability(batch_key: str) -> str:
    return (
        "ACTUAL" if _checkpoint_semantics(batch_key) == "PROVIDER_INGESTION" else "NOT_APPLICABLE"
    )


def _failure_classification_for_checkpoint(batch_key: str, status: str) -> str | None:
    if status == "COMPLETED":
        return None
    return {
        "PROVIDER_INGESTION": "PROVIDER_INGESTION_FAILURE",
        "INSTITUTIONAL_FLOW_PUBLICATION_READBACK": "INSTITUTIONAL_FLOW_READBACK_FAILURE",
        "FORMAL_MARKET_FACTS_PERSISTENCE": "MARKET_FACTS_PERSISTENCE_FAILURE",
        "FINAL_FORMAL_PUBLICATION": "FORMAL_PUBLICATION_READINESS_FAILURE",
    }.get(_checkpoint_semantics(batch_key))


def _readback_failure_metadata(
    *,
    formal_readback: Mapping[str, Any],
    market_facts_publication: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    flow = formal_readback.get("institutionalFlow") or {}
    if flow.get("status") != "PASS":
        return {
            "failureClassification": "INSTITUTIONAL_FLOW_READBACK_FAILURE",
            "failedSection": "institutionalFlow",
            "reasonCode": flow.get("reasonCode") or "INSTITUTIONAL_FLOW_READBACK_UNAVAILABLE",
        }
    if market_facts_publication and market_facts_publication.get("status") != "SUCCESS":
        return {
            "failureClassification": "MARKET_FACTS_PERSISTENCE_FAILURE",
            "failedSection": "marketFactsPublication",
            "reasonCode": market_facts_publication.get("reason")
            or market_facts_publication.get("error")
            or "MARKET_FACTS_PERSISTENCE_UNAVAILABLE",
        }
    if formal_readback.get("status") != "PASS":
        topic = formal_readback.get("topicSnapshot") or {}
        home = formal_readback.get("homePublication") or {}
        strength = formal_readback.get("formalStrength") or {}
        lifecycle = formal_readback.get("formalLifecycle") or {}
        return {
            "failureClassification": "FORMAL_PUBLICATION_READINESS_FAILURE",
            "failedSection": (
                "topicSnapshot"
                if topic.get("status") != "PASS"
                else "homePublication"
                if home.get("status") != "PASS"
                else "formalStrength"
                if strength.get("status") != "PASS"
                else "formalLifecycle"
                if lifecycle.get("status") != "PASS"
                else "formalPublication"
            ),
            "reasonCode": (
                "FORMAL_STRENGTH_NOT_READY"
                if strength.get("status") != "PASS"
                else "FORMAL_LIFECYCLE_NOT_READY"
                if lifecycle.get("status") != "PASS"
                else "FORMAL_PUBLICATION_READBACK_NOT_READY"
            ),
        }
    return {}


@dataclass(frozen=True)
class PostCloseRunResult:
    run_id: str
    status: str
    requested_count: int
    success_count: int
    failure_count: int
    skipped_count: int
    retry_count: int
    provider_point_count: int
    tracking_count: int
    failure_codes: tuple[str, ...]
    snapshot_count: int = 0
    snapshot_status: str = "NOT_RUN"
    snapshot_date: str | None = None
    idempotent_reuse: bool = False
    status_resolution_metrics: Mapping[str, int | float] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "runId": self.run_id,
            "runType": "POST_CLOSE",
            "status": self.status,
            "requestedCount": self.requested_count,
            "successCount": self.success_count,
            "failureCount": self.failure_count,
            "skippedCount": self.skipped_count,
            "retryCount": self.retry_count,
            "providerPointCount": self.provider_point_count,
            "trackingCount": self.tracking_count,
            "failureCodes": list(self.failure_codes),
            "snapshotCount": self.snapshot_count,
            "snapshotStatus": self.snapshot_status,
            "snapshotDate": self.snapshot_date,
            "idempotentReuse": self.idempotent_reuse,
            "statusResolutionMetrics": dict(self.status_resolution_metrics or {}),
        }


class PostClosePreconditionError(RuntimeError):
    """Raised before any post-close write when reference eligibility is unsafe."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def resolve_post_close_run_date(
    now: datetime,
    timezone_name: str,
    explicit_run_date: date | None = None,
) -> date:
    """Bind an automatic POST_CLOSE run to the configured market-local date."""

    if explicit_run_date is not None:
        return explicit_run_date
    if now.tzinfo is None:
        raise ValueError("post-close clock must be timezone-aware")
    return now.astimezone(ZoneInfo(timezone_name)).date()


def _validated_post_close_context(
    session: Session,
    *,
    run_date: date,
    reference_version: str,
):
    try:
        context = load_g2_preflight_context(
            session,
            target_date=run_date,
            reference_version=reference_version,
        )
    except Exception as exc:
        raise PostClosePreconditionError("REFERENCE_PRECONDITION_FAILED") from exc

    if context.reference_result.get("referenceLoadStatus") != "READY":
        raise PostClosePreconditionError("REFERENCE_CONTEXT_NOT_READY")
    if context.eligibility_error is not None:
        raise PostClosePreconditionError("LIFECYCLE_CONTEXT_INVALID")
    if tuple(sorted(market.market_code for market in context.markets)) != ("TPE", "TWO"):
        raise PostClosePreconditionError("CANONICAL_MARKET_CONTEXT_INCOMPLETE")
    if not all(market.context_ready for market in context.markets):
        raise PostClosePreconditionError("MARKET_CONTEXT_NOT_READY")
    return context


def expected_post_close_universe(
    session: Session,
    *,
    run_date: date,
    reference_version: str,
) -> Mapping[str, tuple[str, ...]]:
    """Load the existing fail-closed date-effective reference universe."""

    context = _validated_post_close_context(
        session,
        run_date=run_date,
        reference_version=reference_version,
    )
    return {market.market_code: tuple(market.instrument_codes) for market in context.markets}


class PostCloseUpdater:
    """Run official TWSE/TPEx daily updates without fabricating closed data."""

    def __init__(
        self,
        session: Session,
        config: LiveRuntimeConfig,
        *,
        clock: Callable[[], datetime] | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.session = session
        self.config = config
        self.clock = clock or (lambda: datetime.now(UTC))
        self.sleep = sleep
        self._status_resolution_metrics = StatusResolutionMetrics()
        self._active_run_id: Any | None = None
        self._active_failure_stage = "POST_CLOSE_ORCHESTRATION"
        self._active_run_date: date | None = None
        self._active_execution_scope = NORMAL_CURRENT_DAY
        self._active_execution_key: str | None = None
        self.session_clock = MarketSessionClock(
            config.timezone_name,
            config.session_open,
            config.session_close,
            config.closed_dates,
        )

    def _now(self) -> datetime:
        value = self.clock()
        if value.tzinfo is None:
            raise ValueError("post-close clock must be timezone-aware")
        return value.astimezone(UTC)

    def _instruments(
        self, expected_by_market: Mapping[str, Collection[str]]
    ) -> list[tuple[Instrument, Market]]:
        predicates = [
            and_(Market.code == market_code, Instrument.instrument_code.in_(tuple(codes)))
            for market_code, codes in expected_by_market.items()
            if codes
        ]
        if not predicates:
            raise PostClosePreconditionError("EMPTY_DATE_EFFECTIVE_UNIVERSE")
        return list(
            self.session.execute(
                select(Instrument, Market)
                .join(Market, Market.id == Instrument.market_id)
                .where(
                    Instrument.is_active.is_(True),
                    Market.is_active.is_(True),
                    Market.code.in_(("TPE", "TWO")),
                    Instrument.instrument_type == "EQUITY",
                    or_(*predicates),
                )
                .order_by(Market.code, Instrument.instrument_code)
            ).all()
        )

    @staticmethod
    def _validate_instruments(
        instruments: Collection[tuple[Instrument, Market]],
        expected_by_market: Mapping[str, Collection[str]],
    ) -> None:
        expected = {
            (market_code, instrument_code)
            for market_code, codes in expected_by_market.items()
            for instrument_code in codes
        }
        actual = {(market.code, instrument.instrument_code) for instrument, market in instruments}
        if len(instruments) != len(actual) or actual != expected:
            raise PostClosePreconditionError("DATE_EFFECTIVE_UNIVERSE_MISMATCH")

    @staticmethod
    def _resolve_target_symbols(
        expected_by_market: Mapping[str, Collection[str]],
        requested_symbols: Collection[str] | None,
    ) -> tuple[Mapping[str, tuple[str, ...]] | None, tuple[str, ...]]:
        """Resolve CODE or MARKET:CODE input against the date-effective universe."""

        if requested_symbols is None:
            return None, ()

        expected = {
            (market_code.upper(), str(instrument_code))
            for market_code, codes in expected_by_market.items()
            for instrument_code in codes
        }
        selected: list[tuple[str, str]] = []
        for raw_symbol in requested_symbols:
            token = str(raw_symbol).strip().upper()
            if not token:
                raise PostClosePreconditionError("TARGET_SYMBOL_INVALID")
            if ":" in token:
                market_code, instrument_code = (part.strip() for part in token.split(":", 1))
                if not market_code or not instrument_code:
                    raise PostClosePreconditionError("TARGET_SYMBOL_INVALID")
                identity = (market_code, instrument_code)
            else:
                matches = [identity for identity in expected if identity[1] == token]
                if not matches:
                    raise PostClosePreconditionError("TARGET_SYMBOL_NOT_IN_DATE_EFFECTIVE_UNIVERSE")
                if len(matches) > 1:
                    raise PostClosePreconditionError("TARGET_SYMBOL_MARKET_REQUIRED")
                identity = matches[0]
            if identity not in expected:
                raise PostClosePreconditionError("TARGET_SYMBOL_NOT_IN_DATE_EFFECTIVE_UNIVERSE")
            if identity not in selected:
                selected.append(identity)

        if not selected:
            raise PostClosePreconditionError("TARGET_SYMBOLS_EMPTY")

        selected_by_market: dict[str, list[str]] = {}
        for market_code, instrument_code in selected:
            selected_by_market.setdefault(market_code, []).append(instrument_code)
        normalized = tuple(
            sorted(f"{market_code}:{instrument_code}" for market_code, instrument_code in selected)
        )
        return (
            {market_code: tuple(codes) for market_code, codes in selected_by_market.items()},
            normalized,
        )

    @staticmethod
    def _targetable_universe(
        context: Any,
        run_date: date,
        eligible_by_market: Mapping[str, Collection[str]],
    ) -> Mapping[str, tuple[str, ...]]:
        """Include lifecycle-authorized no-trade identities for targeted runs.

        Full post-close collection deliberately uses only eligible identities.
        An explicit targeted retry also needs to reach an active instrument that
        is suspended, delisted, or terminated on the requested date so the
        ingestion contract can persist its authoritative no-trade state.
        """

        grouped: dict[str, set[str]] = {
            market_code: set(codes) for market_code, codes in eligible_by_market.items()
        }
        for row in context.universe_rows:
            if row.market_code not in grouped:
                continue
            eligibility = evaluate_instrument_eligibility(row, run_date)
            lifecycle_status = resolve_lifecycle_status(row, run_date)
            if eligibility.eligible or lifecycle_status in INELIGIBLE_LIFECYCLE_STATUSES:
                grouped[row.market_code].add(row.instrument_code)
        return {market_code: tuple(sorted(codes)) for market_code, codes in grouped.items()}

    def _execution_key(
        self,
        run_date: date,
        *,
        target_symbols: Collection[str] | None = None,
        execution_mode: str = "MANUAL",
    ) -> str:
        """Return a deterministic identity separated by execution purpose."""

        execution_scope = _execution_scope(execution_mode)
        run_scope = "FULL" if target_symbols is None else "TARGETED"
        scope_suffix = (
            "" if target_symbols is None else f":{stable_hash(tuple(target_symbols))[:32]}"
        )
        prefix = "history-recovery" if execution_scope == HISTORY_RECOVERY else "post-close"
        return (
            f"{prefix}:{self.config.reference_data_version}:"
            f"{self.config.calendar_code}:{run_date.isoformat()}:"
            f"{execution_scope}:{run_scope}{scope_suffix}"
        )

    @staticmethod
    def _checkpoint_key(phase: str, suffix: str | None = None) -> str:
        value = phase if suffix is None else f"{phase}:{suffix}"
        if len(value) > 128:
            raise ValueError("POST_CLOSE_CHECKPOINT_KEY_TOO_LONG")
        return value

    def _latest_checkpoint(
        self,
        run_id: Any,
        batch_key: str,
    ) -> LiveCollectorCheckpoint | None:
        return self.session.scalar(
            select(LiveCollectorCheckpoint)
            .where(
                LiveCollectorCheckpoint.run_id == run_id,
                LiveCollectorCheckpoint.batch_key == batch_key,
            )
            .order_by(
                LiveCollectorCheckpoint.attempt_number.desc(),
                LiveCollectorCheckpoint.created_at.desc(),
                LiveCollectorCheckpoint.id.desc(),
            )
            .limit(1)
        )

    def _checkpoint_event(
        self,
        *,
        run_id: Any,
        batch_key: str,
        status: str,
        batch_number: int | None = None,
        processed_count: int = 0,
        succeeded_count: int = 0,
        failed_count: int = 0,
        skipped_count: int = 0,
        retry_count: int = 0,
        provider_request_count: int | None = None,
        provider_failure_count: int | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> LiveCollectorCheckpoint:
        """Append one immutable checkpoint event and make it durable."""

        if not hasattr(self, "session") or self.session is None:
            return None  # type: ignore[return-value]
        if status not in {"IN_PROGRESS", "COMPLETED", "PARTIAL", "FAILED"}:
            raise ValueError("invalid POST_CLOSE checkpoint status")
        previous_failure_stage = getattr(self, "_active_failure_stage", "POST_CLOSE_ORCHESTRATION")
        self._active_failure_stage = f"{batch_key}_CHECKPOINT"
        latest = self._latest_checkpoint(run_id, batch_key)
        attempt_number = (latest.attempt_number + 1) if latest else 1
        resolved_batch_number = (
            batch_number
            if batch_number is not None
            else _CHECKPOINT_BATCH_NUMBERS.get(batch_key, 1000)
        )
        metadata_payload = dict(metadata or {})
        checkpoint_semantic = _checkpoint_semantics(batch_key)
        execution_scope = getattr(self, "_active_execution_scope", NORMAL_CURRENT_DAY)
        execution_key = getattr(self, "_active_execution_key", None)
        metadata_payload.setdefault("executionScope", execution_scope)
        metadata_payload.setdefault(
            "checkpointNamespace",
            f"{execution_scope}:{execution_key or run_id}",
        )
        if execution_key is not None:
            metadata_payload.setdefault("executionKey", execution_key)
        metadata_payload.setdefault("checkpointSemantic", checkpoint_semantic)
        provider_metrics_applicability = _provider_metrics_applicability(batch_key)
        metadata_payload.setdefault("providerMetricsApplicability", provider_metrics_applicability)
        failure_classification = _failure_classification_for_checkpoint(batch_key, status)
        if failure_classification is not None:
            metadata_payload.setdefault("failureClassification", failure_classification)
        if provider_metrics_applicability == "ACTUAL":
            provider_request_count = 0 if provider_request_count is None else provider_request_count
            provider_failure_count = 0 if provider_failure_count is None else provider_failure_count
            if (
                not isinstance(provider_request_count, int)
                or provider_request_count < 0
                or not isinstance(provider_failure_count, int)
                or provider_failure_count < 0
            ):
                raise ValueError("provider checkpoint counters must be non-negative integers")
        else:
            provider_request_count = None
            provider_failure_count = None
        payload = _json_safe(
            {
                "runId": str(run_id),
                "batchKey": batch_key,
                "batchNumber": resolved_batch_number,
                "attemptNumber": attempt_number,
                "status": status,
                "processedCount": processed_count,
                "succeededCount": succeeded_count,
                "failedCount": failed_count,
                "skippedCount": skipped_count,
                "retryCount": retry_count,
                "providerRequestCount": provider_request_count,
                "providerFailureCount": provider_failure_count,
                "metadata": metadata_payload,
            }
        )
        try:
            checkpoint_hash = checkpoint_stable_hash(payload)
        except Exception:
            self._active_failure_stage = f"{batch_key}_CHECKPOINT_CANONICALIZATION"
            raise
        checkpoint = LiveCollectorCheckpoint(
            run_id=run_id,
            batch_number=resolved_batch_number,
            batch_key=batch_key,
            attempt_number=attempt_number,
            status=status,
            processed_count=processed_count,
            succeeded_count=succeeded_count,
            failed_count=failed_count,
            skipped_count=skipped_count,
            retry_count=retry_count,
            provider_request_count=provider_request_count,
            provider_failure_count=provider_failure_count,
            checkpoint_hash=checkpoint_hash,
            metadata_payload=payload["metadata"],
        )
        self.session.add(checkpoint)
        self.session.commit()
        self._active_failure_stage = previous_failure_stage
        return checkpoint

    def _completed_market_checkpoint_totals(self, run_id: Any) -> dict[str, int]:
        rows = self.session.scalars(
            select(LiveCollectorCheckpoint)
            .where(
                LiveCollectorCheckpoint.run_id == run_id,
                LiveCollectorCheckpoint.batch_key.like("FORMAL_MARKET_FACTS:%"),
            )
            .order_by(
                LiveCollectorCheckpoint.batch_key,
                LiveCollectorCheckpoint.attempt_number,
                LiveCollectorCheckpoint.created_at,
            )
        ).all()
        latest: dict[str, LiveCollectorCheckpoint] = {}
        for row in rows:
            latest[row.batch_key] = row
        completed = [row for row in latest.values() if row.status == "COMPLETED"]
        return {
            "success_count": sum(row.succeeded_count for row in completed),
            "failure_count": sum(row.failed_count for row in completed),
            "skipped_count": sum(row.skipped_count for row in completed),
            "retry_count": sum(row.retry_count for row in completed),
            "point_count": sum((row.provider_request_count or 0) for row in completed),
        }

    @staticmethod
    def _reentry_block_reason(
        metadata: Mapping[str, Any],
        *,
        allow_terminal_recovery: bool,
        execution_mode: str,
    ) -> str | None:
        """Fail closed unless an existing recovery has a durable re-entry contract."""

        if not allow_terminal_recovery or execution_mode != "RECOVERY":
            return None
        contract = metadata.get("reentryContract")
        if not isinstance(contract, Mapping):
            return "POST_CLOSE_REENTRY_REQUIRES_OWNER_REAUTH"
        execution_key = metadata.get("executionKey")
        if contract.get("idempotencyKey") != execution_key:
            return "POST_CLOSE_REENTRY_IDEMPOTENCY_KEY_MISMATCH"
        if contract.get("status") == "OWNER_REAUTH_REQUIRED":
            return "POST_CLOSE_REENTRY_REQUIRES_OWNER_REAUTH"
        if contract.get("eligible") is False:
            return "POST_CLOSE_REENTRY_REQUIRES_OWNER_REAUTH"
        if metadata.get("orchestrationFailure"):
            return "POST_CLOSE_REENTRY_REQUIRES_OWNER_REAUTH"
        return None

    def _mark_run_for_resume(
        self,
        run: LiveCollectorRun,
        now: datetime,
        *,
        recovery_authorization_consumed: bool = False,
    ) -> None:
        metadata = dict(run.metadata_payload or {})
        metadata["resumeCount"] = int(metadata.get("resumeCount", 0) or 0) + 1
        metadata["lastResumeAt"] = now
        reentry_contract = dict(metadata.get("reentryContract") or {})
        reentry_contract.setdefault("idempotencyKey", metadata.get("executionKey"))
        reentry_contract.setdefault("newRecoveryRunAllowed", False)
        reentry_contract.setdefault("providerPointReuse", "COMPLETED_CHECKPOINTS_ONLY")
        reentry_contract.setdefault(
            "providerPointDuplicationRisk", "POSSIBLE_FOR_NON_COMPLETED_BATCHES"
        )
        reentry_contract["status"] = "RESUMING"
        reentry_contract["eligible"] = True
        reentry_contract["operatorActionRequired"] = False
        if recovery_authorization_consumed:
            reentry_contract["recoveryAuthorizationConsumed"] = True
        metadata["reentryContract"] = reentry_contract
        run.status = "RUNNING"
        run.completed_at = None
        run.heartbeat_at = now
        run.updated_at = now
        run.provider_status = "CONNECTING"
        run.failure_code = None
        run.failure_message = None
        run.metadata_payload = _json_safe(metadata)
        self.session.commit()

    def _close_orchestration_failure(self, run_id: Any, exc: Exception) -> None:
        """Close an interrupted run without classifying it as a data failure.

        The existing run status vocabulary has a legal terminal ``FAILED``
        state, so no enum or migration is needed.  This write is deliberately
        separate from checkpoint emission: a checkpoint canonicalization
        error must not prevent the run lifecycle from reaching a terminal
        state, and it must not create a misleading provider checkpoint.
        """

        try:
            self.session.rollback()
            run = self.session.get(LiveCollectorRun, run_id)
            if run is None or run.status != "RUNNING":
                return
            now = self._now()
            stage = getattr(self, "_active_failure_stage", "POST_CLOSE_ORCHESTRATION")
            failure_code = (
                "POST_CLOSE_CHECKPOINT_CANONICALIZATION_FAILED"
                if stage.endswith("_CHECKPOINT_CANONICALIZATION")
                else "POST_CLOSE_RUN_RESUME_FAILED"
                if stage == "RUN_RESUME"
                else "POST_CLOSE_CHECKPOINT_WRITE_FAILED"
                if stage.endswith("_CHECKPOINT")
                else "POST_CLOSE_ORCHESTRATION_FAILED"
            )
            metadata = dict(run.metadata_payload or {})
            try:
                resume_count = int(metadata.get("resumeCount", 0) or 0)
            except (TypeError, ValueError):
                resume_count = 0
            execution_key = metadata.get("executionKey")
            metadata["orchestrationFailure"] = {
                "status": "FAILED",
                "failureClassification": "POST_CLOSE_ORCHESTRATION_FAILURE",
                "failureCode": failure_code,
                "failureStage": stage,
                "exceptionClass": type(exc).__name__,
                "exceptionMessage": str(exc)[:500],
                "runId": str(run_id),
                "previousState": "RUNNING",
                "resumeCount": resume_count,
                "retryReentryEligibility": "OWNER_REAUTH_REQUIRED",
                "operatorActionRequired": True,
            }
            metadata["reentryContract"] = {
                "status": "OWNER_REAUTH_REQUIRED",
                "eligible": False,
                "idempotencyKey": execution_key,
                "newRecoveryRunAllowed": False,
                "providerPointReuse": "COMPLETED_CHECKPOINTS_ONLY",
                "providerPointDuplicationRisk": "POSSIBLE_FOR_NON_COMPLETED_BATCHES",
                "recoveryAuthorizationConsumed": True,
                "operatorActionRequired": True,
            }
            run.status = "FAILED"
            run.completed_at = now
            run.heartbeat_at = now
            run.updated_at = now
            run.provider_status = "ERROR"
            run.freshness_state = "PARTIAL"
            run.failure_code = failure_code
            run.failure_message = f"{type(exc).__name__}: {str(exc)[:500]}"
            run.metadata_payload = _json_safe(metadata)
            self.session.commit()
        except Exception:
            # Preserve the original exception.  If the database is unavailable
            # the next process can still inspect the original failure context.
            with suppress(Exception):
                self.session.rollback()

    def _set_active_run(self, run_id: Any, stage: str = "POST_CLOSE_ORCHESTRATION") -> None:
        self._active_run_id = run_id
        self._active_failure_stage = stage

    def _acquire_session_claim_lock(self, run_date: date) -> None:
        """Serialize first-claim races without adding a second lock table."""

        if self.session.get_bind().dialect.name != "postgresql":
            return
        self.session.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:lock_key)::bigint)"),
            {
                "lock_key": (
                    f"topicpilot:post-close-session:{self.config.reference_data_version}:"
                    f"{self.config.calendar_code}:{run_date.isoformat()}"
                )
            },
        )

    def _runs_for_date(self, run_date: date) -> list[LiveCollectorRun]:
        """Load POST_CLOSE runs for the requested market date.

        The run table predates an explicit run-date column. Keep the
        started-at timestamp as a compatibility key for legacy rows, while
        preferring the explicit ``runDate`` metadata on historical recovery
        rows whose process started on a later calendar date.
        """

        local_start = datetime.combine(
            run_date,
            clock_time.min,
            tzinfo=self.session_clock.timezone,
        ).astimezone(UTC)
        local_end = local_start + timedelta(days=1)
        return list(
            self.session.scalars(
                select(LiveCollectorRun)
                .where(
                    LiveCollectorRun.run_type == "POST_CLOSE",
                    or_(
                        LiveCollectorRun.metadata_payload["runDate"].as_string()
                        == run_date.isoformat(),
                        and_(
                            LiveCollectorRun.metadata_payload["runDate"].as_string().is_(None),
                            LiveCollectorRun.started_at >= local_start,
                            LiveCollectorRun.started_at < local_end,
                        ),
                    ),
                )
                .order_by(LiveCollectorRun.started_at.desc())
            ).all()
        )

    def _find_existing_run(
        self,
        run_date: date,
        *,
        target_symbols: Collection[str] | None = None,
        execution_mode: str = "MANUAL",
    ) -> LiveCollectorRun | None:
        execution_scope = _execution_scope(execution_mode)
        wanted_run_scope = "TARGETED" if target_symbols is not None else "FULL"
        wanted_symbols = tuple(target_symbols or ())
        wanted_execution_key = self._execution_key(
            run_date,
            target_symbols=wanted_symbols if target_symbols is not None else None,
            execution_mode=execution_mode,
        )
        legacy_execution_key = (
            f"post-close:{self.config.reference_data_version}:"
            f"{self.config.calendar_code}:{run_date.isoformat()}:"
            f"{wanted_run_scope}"
            f"{'' if target_symbols is None else ':' + stable_hash(wanted_symbols)[:32]}"
            if execution_scope == NORMAL_CURRENT_DAY
            else None
        )
        for run in self._runs_for_date(run_date):
            metadata = run.metadata_payload or {}
            if (
                metadata.get("executionKey") == wanted_execution_key
                and _metadata_execution_scope(metadata) == execution_scope
            ):
                return run
            if legacy_execution_key is None or metadata.get("executionKey") != legacy_execution_key:
                continue
            if _metadata_execution_scope(metadata) != NORMAL_CURRENT_DAY:
                continue
            if str(metadata.get("scope", "FULL")).upper() != wanted_run_scope:
                continue
            if wanted_run_scope == "TARGETED":
                recorded = tuple(str(item) for item in metadata.get("targetSymbols", ()))
                if recorded != wanted_symbols:
                    continue
            return run
        return None

    def _completed_attempt_summary(
        self,
        run_id: Any,
        expected_instrument_ids: Collection[Any],
    ) -> dict[str, Any] | None:
        """Return terminal per-instrument counts only for a complete run."""

        attempts = self.session.scalars(
            select(LiveCollectorAttempt)
            .where(LiveCollectorAttempt.run_id == run_id)
            .order_by(
                LiveCollectorAttempt.instrument_id,
                LiveCollectorAttempt.updated_at,
                LiveCollectorAttempt.id,
            )
        ).all()
        latest_by_instrument: dict[Any, LiveCollectorAttempt] = {}
        for attempt in attempts:
            if attempt.instrument_id is None:
                return None
            latest_by_instrument[attempt.instrument_id] = attempt

        expected = set(expected_instrument_ids)
        if set(latest_by_instrument) != expected:
            return None
        latest = tuple(latest_by_instrument.values())
        if any(
            attempt.status not in {"SUCCESS", "FAILED", "TIMEOUT", "SKIPPED"} for attempt in latest
        ):
            return None
        failure_codes = tuple(
            sorted({attempt.error_code for attempt in latest if attempt.error_code})
        )
        return {
            "success_count": sum(attempt.status == "SUCCESS" for attempt in latest),
            "failure_count": sum(attempt.status in {"FAILED", "TIMEOUT"} for attempt in latest),
            "skipped_count": sum(attempt.status == "SKIPPED" for attempt in latest),
            "retry_count": sum(attempt.retry_count for attempt in latest),
            "failure_codes": failure_codes,
        }

    @staticmethod
    def _is_recent_run(run: LiveCollectorRun, now: datetime, *, stale_after: int) -> bool:
        heartbeat = run.heartbeat_at
        if heartbeat.tzinfo is None:
            heartbeat = heartbeat.replace(tzinfo=UTC)
        return now - heartbeat.astimezone(UTC) <= timedelta(seconds=stale_after)

    def _existing_result(
        self,
        run: LiveCollectorRun,
        *,
        run_date: date,
    ) -> PostCloseRunResult:
        metadata = dict(run.metadata_payload or {})
        snapshot = metadata.get("topicSnapshot")
        if not isinstance(snapshot, dict):
            snapshot = {}
        codes = metadata.get("failureCodes")
        if not isinstance(codes, list):
            codes = [run.failure_code] if run.failure_code else []
        return PostCloseRunResult(
            str(run.id),
            run.status,
            run.requested_count,
            run.success_count,
            run.failure_count,
            int(metadata.get("skippedCount", 0) or 0),
            run.retry_count,
            int(metadata.get("providerPointCount", 0) or 0),
            0,
            tuple(str(code) for code in codes),
            int(snapshot.get("topicCount", 0) or 0),
            str(snapshot.get("status", "ALREADY_COMPLETED")),
            str(snapshot.get("snapshotDate", run_date.isoformat())),
            bool((metadata.get("forwardAutomation") or {}).get("status") == "SUCCESS"),
            metadata.get("statusResolutionMetrics"),
        )

    def _create_run(
        self,
        requested_count: int,
        started_at: datetime,
        *,
        run_date: date,
        recovery_of_run_id: Any | None = None,
        scope: str = "FULL",
        target_symbols: Collection[str] = (),
        execution_mode: str = "MANUAL",
    ) -> LiveCollectorRun:
        execution_key = self._execution_key(
            run_date,
            target_symbols=target_symbols if scope == "TARGETED" else None,
            execution_mode=execution_mode,
        )
        execution_scope = _execution_scope(execution_mode)
        if execution_scope == HISTORY_RECOVERY and recovery_of_run_id is not None:
            raise PostClosePreconditionError("HISTORY_RECOVERY_CANNOT_REUSE_EXISTING_RUN")
        metadata = {
            "runType": "POST_CLOSE",
            "runDate": run_date.isoformat(),
            "targetDate": run_date.isoformat(),
            "scope": scope,
            "executionScope": execution_scope,
            "executionKey": execution_key,
            "checkpointNamespace": f"{execution_scope}:{execution_key}",
            "homePublicationPolicy": (
                "FORBIDDEN" if execution_scope == HISTORY_RECOVERY else "CURRENT_DAY_ONLY"
            ),
            "sessionIdentity": {
                "sessionDate": run_date.isoformat(),
                "timezone": self.config.timezone_name,
                "sessionCode": self.config.session_code,
                "calendarCode": self.config.calendar_code,
                "authority": "ACTIVE_REFERENCE_PREFLIGHT",
            },
            "checkpointAuthority": "topicpilot.live_collector_checkpoints",
            "phaseModel": list(POST_CLOSE_PHASE_MODEL),
            "forwardRunKey": execution_key if execution_scope == NORMAL_CURRENT_DAY else None,
            "timezone": self.config.timezone_name,
            "sessionCode": self.config.session_code,
            "calendarCode": self.config.calendar_code,
            "postCloseStart": self.config.post_close_start,
            "statusResolutionBudget": {
                "maxAttempts": self.config.status_resolution_max_attempts,
                "maxTotalWaitSeconds": self.config.status_resolution_max_total_wait_seconds,
                "backoffSeconds": self.config.status_resolution_backoff_seconds,
            },
            "reentryContract": {
                "status": "INITIAL",
                "eligible": True,
                "idempotencyKey": execution_key,
                "newRecoveryRunAllowed": False,
                "providerPointReuse": "COMPLETED_CHECKPOINTS_ONLY",
                "providerPointDuplicationRisk": "POSSIBLE_FOR_NON_COMPLETED_BATCHES",
                "recoveryAuthorizationConsumed": execution_mode == "RECOVERY",
                "operatorActionRequired": False,
            },
            "executionMode": execution_mode,
            "calendarAuthority": "ACTIVE_REFERENCE_PREFLIGHT",
            "lifecycleAuthority": "ACTIVE_REFERENCE_PREFLIGHT",
            "batchSize": self.config.history_batch_size,
            "skippedCount": 0,
            "sourceProviders": {"TPE": "TWSE_OFFICIAL_DAILY", "TWO": "TPEX_OFFICIAL_DAILY"},
        }
        if scope == "TARGETED":
            metadata["targetSymbols"] = list(target_symbols)
        if recovery_of_run_id is not None:
            metadata["recoveryOfRunId"] = str(recovery_of_run_id)
        if recovery_of_run_id is None:
            metadata["recoveryStrategy"] = (
                "NEW_HISTORY_RUN"
                if execution_scope == HISTORY_RECOVERY
                else "NORMAL_CURRENT_DAY"
            )
        else:
            metadata["recoveryStrategy"] = "EXPLICIT_RECOVERY_REFERENCE"
        run = LiveCollectorRun(
            id=uuid5(NAMESPACE_URL, f"topicpilot:{execution_key}"),
            run_type="POST_CLOSE",
            status="RUNNING",
            provider_code="OFFICIAL_DAILY_ROUTER",
            adapter_version="official-daily-router.v1",
            config_hash=stable_hash(
                {
                    "historyBatchSize": self.config.history_batch_size,
                    "historyRequestsPerMinute": self.config.history_requests_per_minute,
                    "historyMinRequestIntervalSeconds": (
                        str(self.config.history_min_request_interval_seconds)
                    ),
                    "historyMaxRetries": self.config.history_max_retries,
                    "historyRetryBackoffSeconds": str(self.config.history_retry_backoff_seconds),
                    "statusResolutionMaxAttempts": self.config.status_resolution_max_attempts,
                    "statusResolutionMaxTotalWaitSeconds": str(
                        self.config.status_resolution_max_total_wait_seconds
                    ),
                    "statusResolutionBackoffSeconds": str(
                        self.config.status_resolution_backoff_seconds
                    ),
                }
            ),
            started_at=started_at,
            heartbeat_at=started_at,
            requested_count=requested_count,
            freshness_state="UNKNOWN",
            provider_status="CONNECTING",
            metadata_payload=metadata,
        )
        self.session.add(run)
        self.session.flush()
        self.session.commit()
        return run

    def _create_or_get_run(
        self,
        requested_count: int,
        started_at: datetime,
        *,
        run_date: date,
        scope: str,
        target_symbols: Collection[str],
        execution_mode: str,
    ) -> tuple[LiveCollectorRun, bool]:
        """Create one deterministic run row, or converge on a concurrent creator."""

        try:
            return (
                self._create_run(
                    requested_count,
                    started_at,
                    run_date=run_date,
                    scope=scope,
                    target_symbols=target_symbols,
                    execution_mode=execution_mode,
                ),
                True,
            )
        except IntegrityError:
            self.session.rollback()
            execution_key = self._execution_key(
                run_date,
                target_symbols=target_symbols if scope == "TARGETED" else None,
                execution_mode=execution_mode,
            )
            existing = self.session.get(
                LiveCollectorRun,
                uuid5(NAMESPACE_URL, f"topicpilot:{execution_key}"),
            )
            if existing is None:
                raise
            return existing, False

    def _idempotent_result(self, run_date: date) -> PostCloseRunResult | None:
        run_key = self._execution_key(run_date, execution_mode="SCHEDULED")
        legacy_run_key = (
            f"post-close:{self.config.reference_data_version}:"
            f"{self.config.calendar_code}:{run_date.isoformat()}"
        )
        runs = self.session.scalars(
            select(LiveCollectorRun)
            .where(
                LiveCollectorRun.run_type == "POST_CLOSE",
                LiveCollectorRun.status == "SUCCESS",
            )
            .order_by(LiveCollectorRun.started_at.desc())
        ).all()
        for run in runs:
            metadata = run.metadata_payload or {}
            forward = metadata.get("forwardAutomation") or {}
            if (
                metadata.get("forwardRunKey") not in {run_key, legacy_run_key}
                and metadata.get("executionKey") not in {run_key, legacy_run_key}
            ) or forward.get("status") != "SUCCESS":
                continue
            snapshot = metadata.get("topicSnapshot") or {}
            return PostCloseRunResult(
                str(run.id),
                "SUCCESS",
                int(run.requested_count or 0),
                int(run.success_count or 0),
                int(run.failure_count or 0),
                int(metadata.get("skippedCount", 0)),
                int(run.retry_count or 0),
                int(metadata.get("providerPointCount", 0)),
                0,
                (),
                int(snapshot.get("topicCount", 0)),
                str(snapshot.get("status", "SUCCESS")),
                run_date.isoformat(),
                True,
                metadata.get("statusResolutionMetrics"),
            )
        return None

    @staticmethod
    def _history_attempt_outcome(
        result: HistoricalInstrumentResult,
    ) -> tuple[str, str | None, str | None]:
        """Translate one batched-ingestion result into the audit vocabulary."""

        if result.covered_count:
            error_code = (
                "APPROVED_NO_TRADE"
                if result.instrument_status in LEGITIMATE_UNAVAILABLE_CODES
                and result.priced_count == 0
                else None
            )
            return "SUCCESS", error_code, result.status_reason
        return (
            "SKIPPED",
            "MISSING_MARKET_DATA",
            result.status_reason
            or (
                "official provider returned no priced bar and no "
                "lifecycle-authorized no-trade evidence"
            ),
        )

    @staticmethod
    def _is_market_batch_provider_failure(exc: Exception, adapter: Any) -> bool:
        """Avoid per-symbol fallback when the shared market request failed."""

        code = getattr(exc, "code", None)
        return bool(
            getattr(adapter, "market_batch", False)
            and isinstance(code, str)
            and code
            in {
                "EXCHANGE_EMPTY_PAYLOAD",
                "EXCHANGE_NO_DATA",
                "EXCHANGE_NOT_READY",
                "DUPLICATE_INSTRUMENT_ROW",
                "INVALID_DATE",
                "INVALID_NUMBER",
                "INVALID_OHLC",
                "INVALID_PAYLOAD",
                "INVALID_VOLUME",
                "PROVIDER_DATE_MISMATCH",
                "PROVIDER_REQUEST_FAILED",
            }
        )

    def _record_history_attempt(
        self,
        *,
        run_id: Any,
        instrument: Instrument,
        market: Market,
        started_at: datetime,
        completed_at: datetime,
        attempt_status: str,
        retry_count: int,
        error_code: str | None,
        error_message: str | None,
        provider_status: str,
    ) -> None:
        self.session.add(
            LiveCollectorAttempt(
                run_id=run_id,
                instrument_id=instrument.id,
                instrument_code=instrument.instrument_code,
                market_code=market.code,
                attempt_number=retry_count + 1,
                status=attempt_status,
                started_at=started_at,
                retrieved_at=completed_at if attempt_status == "SUCCESS" else None,
                updated_at=completed_at,
                observed_at=None,
                latency_ms=max(0, int((completed_at - started_at).total_seconds() * 1000)),
                retry_count=retry_count,
                provider_status=provider_status,
                freshness_state="FRESH" if attempt_status == "SUCCESS" else "UNKNOWN",
                error_code=error_code,
                error_message=error_message,
            )
        )

    def _stale_after_seconds(self) -> int:
        """Use the existing bounded provider/worker budget as the lease bound."""

        return max(
            self.config.poll_interval_seconds * 2,
            int(self.config.provider_timeout_seconds)
            * max(1, self.config.history_batch_size)
            * (self.config.history_max_retries + 1),
        )

    def _ensure_completed_checkpoint(
        self,
        *,
        run_id: Any,
        batch_key: str,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        if not hasattr(self, "session") or self.session is None:
            return
        latest = self._latest_checkpoint(run_id, batch_key)
        if latest is not None and latest.status == "COMPLETED":
            return
        self._checkpoint_event(
            run_id=run_id,
            batch_key=batch_key,
            status="COMPLETED",
            metadata=metadata,
        )

    def _prepare_run(
        self,
        *,
        run_date: date,
        now: datetime,
        requested_count: int,
        target_symbols: Collection[str],
        is_targeted: bool,
        allow_terminal_recovery: bool,
        execution_mode: str,
        context: Any,
    ) -> tuple[LiveCollectorRun, bool, dict[str, int]]:
        """Claim the session run and return durable progress totals.

        New and recovered executions share one deterministic run identity.  A
        stale RUNNING row is resumed in place; a recent RUNNING row remains an
        active lease and blocks a duplicate worker.
        """

        self._acquire_session_claim_lock(run_date)
        existing_run = self._find_existing_run(
            run_date,
            target_symbols=target_symbols if is_targeted else None,
            execution_mode=execution_mode,
        )
        active_other_scope = next(
            (
                run
                for run in self._runs_for_date(run_date)
                if run.status == "RUNNING"
                and (existing_run is None or run.id != existing_run.id)
            ),
            None,
        )
        if active_other_scope is not None:
            raise PostClosePreconditionError("POST_CLOSE_RUN_IN_PROGRESS")

        if existing_run is not None:
            existing_run = (
                self.session.scalar(
                    select(LiveCollectorRun)
                    .where(LiveCollectorRun.id == existing_run.id)
                    .with_for_update()
                )
                or existing_run
            )
            self._set_active_run(existing_run.id)
            metadata = existing_run.metadata_payload or {}
            forward_status = (metadata.get("forwardAutomation") or {}).get("status")
            safely_complete = (
                existing_run.status == "SUCCESS" and forward_status == "SUCCESS"
            ) or (existing_run.status == "MARKET_CLOSED" and not context.target_date_is_session)
            if safely_complete or (
                existing_run.status in {"SUCCESS", "PARTIAL", "FAILED", "MARKET_CLOSED"}
                and not allow_terminal_recovery
            ):
                return existing_run, True, {}
            if existing_run.status == "RUNNING" and self._is_recent_run(
                existing_run,
                now,
                stale_after=self._stale_after_seconds(),
            ):
                raise PostClosePreconditionError("POST_CLOSE_RUN_IN_PROGRESS")
            reentry_block_reason = self._reentry_block_reason(
                metadata,
                allow_terminal_recovery=allow_terminal_recovery,
                execution_mode=execution_mode,
            )
            if reentry_block_reason is not None:
                raise PostClosePreconditionError(reentry_block_reason)
            if existing_run.failure_code == "POST_CLOSE_FINALIZATION_FAILED":
                # Preserve the existing recovery diagnostic while resuming the
                # same deterministic run identity and checkpoint stream.
                metadata = dict(existing_run.metadata_payload or {})
                metadata["resumeReason"] = "POST_CLOSE_FINALIZATION_FAILED"
                existing_run.metadata_payload = _json_safe(metadata)
                self.session.commit()
            self._active_failure_stage = "RUN_RESUME"
            self._mark_run_for_resume(
                existing_run,
                now,
                recovery_authorization_consumed=(execution_mode == "RECOVERY"),
            )
            self._active_failure_stage = "POST_CLOSE_ORCHESTRATION"
            return (
                existing_run,
                True,
                self._completed_market_checkpoint_totals(existing_run.id),
            )

        run, created = self._create_or_get_run(
            requested_count,
            now,
            run_date=run_date,
            scope="TARGETED" if is_targeted else "FULL",
            target_symbols=target_symbols,
            execution_mode=execution_mode,
        )
        if not created:
            self._set_active_run(run.id)
            if run.status == "RUNNING":
                raise PostClosePreconditionError("POST_CLOSE_RUN_IN_PROGRESS")
            if run.status in {"SUCCESS", "PARTIAL", "FAILED", "MARKET_CLOSED"}:
                if not allow_terminal_recovery:
                    return run, True, {}
                metadata = run.metadata_payload or {}
                reentry_block_reason = self._reentry_block_reason(
                    metadata,
                    allow_terminal_recovery=allow_terminal_recovery,
                    execution_mode=execution_mode,
                )
                if reentry_block_reason is not None:
                    raise PostClosePreconditionError(reentry_block_reason)
                self._active_failure_stage = "RUN_RESUME"
                self._mark_run_for_resume(
                    run,
                    now,
                    recovery_authorization_consumed=(execution_mode == "RECOVERY"),
                )
                self._active_failure_stage = "POST_CLOSE_ORCHESTRATION"
                return run, True, self._completed_market_checkpoint_totals(run.id)
        else:
            self._set_active_run(run.id)
        return run, False, {}

    def run_once(
        self,
        *,
        run_date: date | None = None,
        allow_terminal_recovery: bool = False,
        target_symbols: Collection[str] | None = None,
        execution_mode: str = "MANUAL",
    ) -> PostCloseRunResult:
        """Execute one run and close any post-claim orchestration failure."""

        self._active_run_id = None
        self._active_failure_stage = "POST_CLOSE_ORCHESTRATION"
        self._active_run_date = None
        self._active_execution_scope = NORMAL_CURRENT_DAY
        self._active_execution_key = None
        try:
            return self._run_once(
                run_date=run_date,
                allow_terminal_recovery=allow_terminal_recovery,
                target_symbols=target_symbols,
                execution_mode=execution_mode,
            )
        except PostClosePreconditionError:
            # A precondition rejection is not a run failure and must not create
            # a terminal audit row for a run that did not execute.
            raise
        except Exception as exc:
            if self._active_run_id is not None:
                self._close_orchestration_failure(self._active_run_id, exc)
            raise
        finally:
            self._active_run_id = None
            self._active_failure_stage = "POST_CLOSE_ORCHESTRATION"
            self._active_run_date = None
            self._active_execution_scope = NORMAL_CURRENT_DAY
            self._active_execution_key = None

    def _run_once(
        self,
        *,
        run_date: date | None = None,
        allow_terminal_recovery: bool = False,
        target_symbols: Collection[str] | None = None,
        execution_mode: str = "MANUAL",
    ) -> PostCloseRunResult:
        if allow_terminal_recovery and run_date is None:
            raise ValueError("POST_CLOSE_RECOVERY_REQUIRES_EXPLICIT_RUN_DATE")
        now = self._now()
        if execution_mode not in {"SCHEDULED", "MANUAL", "RECOVERY"}:
            raise ValueError("invalid POST_CLOSE execution_mode")
        local_date = resolve_post_close_run_date(
            now,
            self.config.timezone_name,
            run_date,
        )
        context = _validated_post_close_context(
            self.session,
            run_date=local_date,
            reference_version=self.config.reference_data_version,
        )
        expected_by_market = {
            market.market_code: tuple(market.instrument_codes) for market in context.markets
        }
        target_universe = (
            self._targetable_universe(context, local_date, expected_by_market)
            if target_symbols is not None
            else expected_by_market
        )
        selected_by_market, normalized_target_symbols = self._resolve_target_symbols(
            target_universe,
            target_symbols,
        )
        is_targeted = selected_by_market is not None
        self._active_run_date = local_date
        self._active_execution_scope = _execution_scope(execution_mode)
        self._active_execution_key = self._execution_key(
            local_date,
            target_symbols=normalized_target_symbols if is_targeted else None,
            execution_mode=execution_mode,
        )
        requested_by_market = selected_by_market or expected_by_market
        instruments = self._instruments(requested_by_market)
        self._validate_instruments(instruments, requested_by_market)
        eligible_instrument_ids = tuple(instrument.id for instrument, _market in instruments)
        idempotent = (
            None
            if is_targeted or execution_mode == "RECOVERY"
            else self._idempotent_result(local_date)
        )
        if idempotent is not None:
            return idempotent
        run, reused, recovered_counts = self._prepare_run(
            run_date=local_date,
            now=now,
            requested_count=len(instruments),
            target_symbols=normalized_target_symbols,
            is_targeted=is_targeted,
            allow_terminal_recovery=allow_terminal_recovery,
            execution_mode=execution_mode,
            context=context,
        )
        if reused and run.status not in {"RUNNING"}:
            return self._existing_result(run, run_date=local_date)
        run_id = run.id
        run_metadata = run.metadata_payload or {}
        self._active_execution_scope = _metadata_execution_scope(run_metadata)
        self._active_execution_key = str(
            run_metadata.get("executionKey") or self._active_execution_key
        )
        failure_codes: list[str] = []
        success_count = recovered_counts.get("success_count", 0)
        failure_count = recovered_counts.get("failure_count", 0)
        skipped_count = recovered_counts.get("skipped_count", 0)
        retry_count = recovered_counts.get("retry_count", 0)
        point_count = recovered_counts.get("point_count", 0)
        status_resolution_candidates: dict[Any, bool] = {}
        self._ensure_completed_checkpoint(
            run_id=run_id,
            batch_key="SESSION_VALIDATION",
            metadata={
                "sessionDate": local_date,
                "targetDateIsSession": context.target_date_is_session,
                "targetDateReason": context.target_date_reason,
            },
        )
        self._ensure_completed_checkpoint(
            run_id=run_id,
            batch_key="INPUT_READINESS",
            metadata={
                "instrumentCount": len(instruments),
                "scope": "TARGETED" if is_targeted else "FULL",
            },
        )

        session_status = self.session_clock.status(
            datetime.combine(local_date, clock_time(13, 30), tzinfo=self.session_clock.timezone)
        )
        if not context.target_date_is_session or session_status.reason in {
            "WEEKEND",
            "CONFIGURED_CLOSED_DATE",
        }:
            skipped_count = len(instruments)
            status = "MARKET_CLOSED"
            reconciliation = reconcile_daily_market(
                self.session,
                local_date,
                market_closed=True,
                expected_instrument_ids=eligible_instrument_ids,
            )
            snapshot_result = {
                "snapshotDate": local_date.isoformat(),
                "topicCount": 0,
                "status": "NOT_RUN_MARKET_CLOSED",
            }
            self._checkpoint_event(
                run_id=run_id,
                batch_key="FINAL_PUBLICATION",
                status="COMPLETED",
                metadata={
                    "outcome": "MARKET_CLOSED",
                    "publication": "NOT_RUN",
                    "reason": context.target_date_reason or session_status.reason,
                },
            )
            self._finish(
                run_id,
                status=status,
                success_count=0,
                failure_count=0,
                skipped_count=skipped_count,
                retry_count=0,
                point_count=0,
                failure_codes=(context.target_date_reason or "MARKET_CLOSED",),
                snapshot_result=snapshot_result,
                reconciliation=reconciliation,
                now=now,
            )
            self._checkpoint_event(
                run_id=run_id,
                batch_key="COMPLETION",
                status="COMPLETED",
                metadata={"runStatus": status, "formalReadback": "NOT_APPLICABLE"},
            )
            return PostCloseRunResult(
                str(run_id),
                status,
                len(instruments),
                0,
                0,
                skipped_count,
                0,
                0,
                0,
                (context.target_date_reason or "MARKET_CLOSED",),
                snapshot_result.get("topicCount", 0),
                snapshot_result.get("status", "FAILED"),
                local_date.isoformat(),
                False,
                getattr(self, "_status_resolution_metrics", StatusResolutionMetrics()).to_dict(),
            )

        transport = RateLimitedTransport(
            _official_transport,
            requests_per_minute=self.config.history_requests_per_minute,
            min_interval_seconds=self.config.history_min_request_interval_seconds,
            max_retries=self.config.history_max_retries,
            retry_backoff_seconds=self.config.history_retry_backoff_seconds,
            sleep=self.sleep,
        )
        registry = build_historical_provider_registry(
            start_date=local_date,
            end_date=local_date,
            exchange_transport=transport,
            market_batch=True,
            readiness_max_attempts=self.config.history_readiness_max_attempts,
            readiness_max_total_wait_seconds=self.config.history_readiness_max_total_wait_seconds,
            readiness_backoff_seconds=self.config.history_readiness_backoff_seconds,
            readiness_sleep=self.sleep,
        )
        policy = MappingPolicy(
            mapping_policy_version=HISTORICAL_MAPPING_POLICY_VERSION,
            session_code=self.config.session_code,
            calendar_code=self.config.calendar_code,
        )

        market_batches: list[list[tuple[Instrument, Market]]] = []
        for market_code in ("TPE", "TWO"):
            market_instruments = [item for item in instruments if item[1].code == market_code]
            for batch_start in range(0, len(market_instruments), self.config.history_batch_size):
                market_batches.append(
                    market_instruments[batch_start : batch_start + self.config.history_batch_size]
                )

        for batch_index, batch in enumerate(market_batches, start=1):
            market = batch[0][1]
            batch_key = self._checkpoint_key("FORMAL_MARKET_FACTS", f"{market.code}:{batch_index}")
            previous_checkpoint = self._latest_checkpoint(run_id, batch_key)
            if previous_checkpoint is not None and previous_checkpoint.status == "COMPLETED":
                success_count += previous_checkpoint.succeeded_count
                failure_count += previous_checkpoint.failed_count
                skipped_count += previous_checkpoint.skipped_count
                retry_count += previous_checkpoint.retry_count
                point_count += previous_checkpoint.provider_request_count or 0
                continue
            self._checkpoint_event(
                run_id=run_id,
                batch_key=batch_key,
                batch_number=100 + batch_index,
                status="IN_PROGRESS",
                metadata={
                    "market": market.code,
                    "symbols": [instrument.instrument_code for instrument, _ in batch],
                    "sessionDate": local_date,
                },
            )
            registration = registry.for_market(market.code)[0]
            batch_started = self._now()
            retries_before = transport.retry_count
            readiness_retries_before = getattr(registration.adapter, "readiness_retry_count", 0)
            batch_retry_count = 0
            batch_success_count = 0
            batch_skipped_count = 0
            batch_point_count = 0
            try:
                # One transaction covers the whole provider batch.  A single
                # provider/normalizer failure falls back to savepoint-isolated
                # single-instrument writes below, so one bad symbol cannot
                # discard its neighbours' valid bars.
                with self.session.begin():
                    result = ingest_historical(
                        self.session,
                        registration.adapter,
                        [
                            (instrument.instrument_code, item_market.code)
                            for instrument, item_market in batch
                        ],
                        reference_data_version=self.config.reference_data_version,
                        requested_from=local_date,
                        requested_to=local_date,
                        policy=policy,
                        registration=HistoricalSourceRegistration(
                            registration.code,
                            registration.adapter.adapter_version,
                            licensing_classification="OFFICIAL_PUBLIC",
                        ),
                    )
                    summaries = {
                        (item.instrument_code, item.market_code): item
                        for item in result.instrument_results
                    }
                    expected_keys = {
                        (instrument.instrument_code, item_market.code)
                        for instrument, item_market in batch
                    }
                    if set(summaries) != expected_keys:
                        raise RuntimeError("BATCH_RESULT_MISMATCH")
                    batch_retry_count = (
                        transport.retry_count
                        - retries_before
                        + getattr(registration.adapter, "readiness_retry_count", 0)
                        - readiness_retries_before
                    )
                    completed = self._now()
                    for index, (instrument, item_market) in enumerate(batch):
                        summary = summaries[(instrument.instrument_code, item_market.code)]
                        attempt_status, error_code, error_message = self._history_attempt_outcome(
                            summary
                        )
                        self._record_history_attempt(
                            run_id=run_id,
                            instrument=instrument,
                            market=item_market,
                            started_at=batch_started,
                            completed_at=completed,
                            attempt_status=attempt_status,
                            retry_count=batch_retry_count if index == 0 else 0,
                            error_code=error_code,
                            error_message=error_message,
                            provider_status=summary.instrument_status,
                        )
                        if attempt_status == "SUCCESS":
                            batch_success_count += 1
                        else:
                            batch_skipped_count += 1
                            status_resolution_candidates[instrument.id] = error_code in {
                                "PROVIDER_ERROR",
                                "EXCHANGE_NOT_READY",
                                "PROVIDER_REQUEST_FAILED",
                            }
                            if is_targeted and error_code:
                                failure_codes.append(error_code)
                batch_point_count = result.provider_point_count
                success_count += batch_success_count
                skipped_count += batch_skipped_count
                point_count += batch_point_count
                retry_count += batch_retry_count
                self._checkpoint_event(
                    run_id=run_id,
                    batch_key=batch_key,
                    batch_number=100 + batch_index,
                    status="COMPLETED" if batch_skipped_count == 0 else "PARTIAL",
                    processed_count=len(batch),
                    succeeded_count=batch_success_count,
                    skipped_count=batch_skipped_count,
                    retry_count=batch_retry_count,
                    provider_request_count=batch_point_count,
                    metadata={"market": market.code, "sessionDate": local_date},
                )
            except Exception as exc:
                provider_exception = exc
                batch_retry_count = (
                    transport.retry_count
                    - retries_before
                    + getattr(registration.adapter, "readiness_retry_count", 0)
                    - readiness_retries_before
                )
                retry_count += batch_retry_count
                self.session.rollback()

                if provider_exception is not None and self._is_market_batch_provider_failure(
                    provider_exception, registration.adapter
                ):
                    provider_error_code = str(provider_exception.code)
                    provider_error_message = str(provider_exception)
                    fallback_failure_count = 0
                    with self.session.begin():
                        completed = self._now()
                        for instrument, item_market in batch:
                            status_resolution_candidates[instrument.id] = True
                            self._record_history_attempt(
                                run_id=run_id,
                                instrument=instrument,
                                market=item_market,
                                started_at=batch_started,
                                completed_at=completed,
                                attempt_status="FAILED",
                                retry_count=0,
                                error_code=provider_error_code,
                                error_message=provider_error_message,
                                provider_status="ERROR",
                            )
                            fallback_failure_count += 1
                    failure_codes.append(provider_error_code)
                    failure_count += fallback_failure_count
                    self._checkpoint_event(
                        run_id=run_id,
                        batch_key=batch_key,
                        batch_number=100 + batch_index,
                        status="FAILED",
                        processed_count=len(batch),
                        failed_count=fallback_failure_count,
                        retry_count=batch_retry_count,
                        provider_failure_count=1,
                        metadata={
                            "market": market.code,
                            "sessionDate": local_date,
                            "providerErrorCode": provider_error_code,
                        },
                    )
                    self._heartbeat(run_id, self._now())
                    continue

                # Preserve the old per-symbol failure isolation only for a
                # batch that could not be committed as a unit.  In the normal
                # case the path above performs one provider batch and one DB
                # commit for up to ``history_batch_size`` symbols.
                fallback_success_count = 0
                fallback_skipped_count = 0
                fallback_failure_count = 0
                fallback_point_count = 0
                with self.session.begin():
                    for instrument, item_market in batch:
                        item_started = self._now()
                        item_retries_before = transport.retry_count
                        item_readiness_retries_before = getattr(
                            registration.adapter, "readiness_retry_count", 0
                        )
                        attempt_status = "FAILED"
                        error_code: str | None = None
                        error_message: str | None = None
                        provider_status = "ERROR"
                        try:
                            savepoint = self.session.begin_nested()
                            try:
                                single_result = ingest_historical(
                                    self.session,
                                    registration.adapter,
                                    [(instrument.instrument_code, item_market.code)],
                                    reference_data_version=self.config.reference_data_version,
                                    requested_from=local_date,
                                    requested_to=local_date,
                                    policy=policy,
                                    registration=HistoricalSourceRegistration(
                                        registration.code,
                                        registration.adapter.adapter_version,
                                        licensing_classification="OFFICIAL_PUBLIC",
                                    ),
                                )
                                if len(single_result.instrument_results) != 1:
                                    raise RuntimeError("BATCH_RESULT_MISMATCH")
                            except Exception:
                                savepoint.rollback()
                                raise
                            else:
                                savepoint.commit()
                            summary = single_result.instrument_results[0]
                            (
                                attempt_status,
                                error_code,
                                error_message,
                            ) = self._history_attempt_outcome(summary)
                            provider_status = summary.instrument_status
                            fallback_point_count += single_result.provider_point_count
                            if attempt_status == "SUCCESS":
                                fallback_success_count += 1
                            else:
                                fallback_skipped_count += 1
                                if is_targeted and error_code:
                                    failure_codes.append(error_code)
                        except Exception as exc:
                            fallback_failure_count += 1
                            error_code = getattr(exc, "code", type(exc).__name__)
                            error_message = str(exc)
                            status_resolution_candidates[instrument.id] = True
                            failure_codes.append(error_code)
                        completed = self._now()
                        item_retry_count = (
                            transport.retry_count
                            - item_retries_before
                            + getattr(registration.adapter, "readiness_retry_count", 0)
                            - item_readiness_retries_before
                        )
                        retry_count += item_retry_count
                        self._record_history_attempt(
                            run_id=run_id,
                            instrument=instrument,
                            market=item_market,
                            started_at=item_started,
                            completed_at=completed,
                            attempt_status=attempt_status,
                            retry_count=item_retry_count,
                            error_code=error_code,
                            error_message=error_message,
                            provider_status=provider_status,
                        )
                success_count += fallback_success_count
                skipped_count += fallback_skipped_count
                failure_count += fallback_failure_count
                point_count += fallback_point_count
                self._checkpoint_event(
                    run_id=run_id,
                    batch_key=batch_key,
                    batch_number=100 + batch_index,
                    status=(
                        "COMPLETED"
                        if fallback_failure_count == 0 and fallback_skipped_count == 0
                        else "PARTIAL"
                        if fallback_success_count or fallback_skipped_count
                        else "FAILED"
                    ),
                    processed_count=len(batch),
                    succeeded_count=fallback_success_count,
                    failed_count=fallback_failure_count,
                    skipped_count=fallback_skipped_count,
                    retry_count=batch_retry_count,
                    provider_request_count=fallback_point_count,
                    provider_failure_count=fallback_failure_count,
                    metadata={"market": market.code, "sessionDate": local_date},
                )
            self._heartbeat(run_id, self._now())

        bounded_status_resolution = self._resolve_missing_statuses(
            run_id=run_id,
            trading_date=local_date,
            candidates=status_resolution_candidates,
        )
        if bounded_status_resolution is not None:
            legitimate_count = bounded_status_resolution.metrics.legitimate_unavailable_count
            success_count += legitimate_count
            skipped_count = max(0, skipped_count - legitimate_count)
            if legitimate_count:
                failure_codes = [code for code in failure_codes if code != "MISSING_MARKET_DATA"]

        if is_targeted:
            return self._finalize_targeted_run(
                run_id=run_id,
                local_date=local_date,
                requested_count=len(instruments),
                success_count=success_count,
                failure_count=failure_count,
                skipped_count=skipped_count,
                retry_count=retry_count,
                point_count=point_count,
                failure_codes=tuple(sorted(set(failure_codes))),
            )

        return self._finalize_collected_run(
            run_id=run_id,
            local_date=local_date,
            eligible_instrument_ids=eligible_instrument_ids,
            success_count=success_count,
            failure_count=failure_count,
            skipped_count=skipped_count,
            retry_count=retry_count,
            point_count=point_count,
            failure_codes=tuple(sorted(set(failure_codes))),
        )

    def _heartbeat(self, run_id: Any, now: datetime) -> None:
        run = self.session.get(LiveCollectorRun, run_id)
        if run is None or run.status != "RUNNING":
            return
        run.heartbeat_at = now
        run.updated_at = now
        self.session.commit()

    def _resolve_missing_statuses(
        self,
        *,
        run_id: Any,
        trading_date: date,
        candidates: Mapping[Any, bool],
    ):
        """Resolve only missing-price candidates in a separate bounded window."""

        self._status_resolution_by_instrument_id = {}
        if not candidates:
            self._status_resolution_metrics = StatusResolutionMetrics()
            return None
        self._checkpoint_event(
            run_id=run_id,
            batch_key="STATUS_RESOLUTION",
            batch_number=120,
            status="IN_PROGRESS",
            metadata={
                "tradingDate": trading_date,
                "candidateCount": len(candidates),
                "maxAttempts": self.config.status_resolution_max_attempts,
                "maxTotalWaitSeconds": self.config.status_resolution_max_total_wait_seconds,
                "backoffSeconds": self.config.status_resolution_backoff_seconds,
                "separateFromPriceReadiness": True,
            },
        )

        def lookup():
            try:
                rows = read_effective_trading_status_authority(
                    self.session,
                    trading_date,
                    expected_instrument_ids=tuple(candidates),
                    provider_failure_instrument_ids=(
                        instrument_id
                        for instrument_id, provider_failed in candidates.items()
                        if provider_failed
                    ),
                )
                # Convert the operator projection back through the pure
                # resolver contract.  The read model is already the
                # canonical effective decision; no frontend re-derivation
                # is involved.
                converted: list[TradingStatusResolution] = []
                for item in rows:
                    resolution = TradingStatusResolution(
                        status=str(item["resolvedStatus"]),
                        authority_source=item.get("authoritySource"),
                        reason_code=str(item["reasonCode"]),
                        effective_from=item.get("effectiveFrom"),
                        effective_to=item.get("effectiveTo"),
                        source_reference=item.get("sourceReference"),
                        resolution_state=str(item["resolutionState"]),
                        blocks_publication=bool(item["blocksPublication"]),
                        is_legitimate_unavailable=bool(item["isLegitimateUnavailable"]),
                        authority_class=(str(item.get("authorityClass") or "NONE")),
                    )
                    converted.append(resolution)
                    instrument_id = item.get("instrumentId")
                    if instrument_id is not None:
                        self._status_resolution_by_instrument_id[instrument_id] = resolution
                return tuple(converted)
            except Exception as exc:
                raise TradingStatusAuthorityError("STATUS_AUTHORITY_PROVIDER_FAILURE") from exc

        bounded = resolve_missing_statuses_with_budget(
            lookup,
            candidate_count=len(candidates),
            max_attempts=self.config.status_resolution_max_attempts,
            max_total_wait_seconds=self.config.status_resolution_max_total_wait_seconds,
            backoff_seconds=self.config.status_resolution_backoff_seconds,
            sleep=self.sleep,
        )
        self._status_resolution_metrics = bounded.metrics
        self._checkpoint_event(
            run_id=run_id,
            batch_key="STATUS_RESOLUTION",
            batch_number=120,
            status=(
                "COMPLETED" if bounded.metrics.unresolved_unavailable_count == 0 else "PARTIAL"
            ),
            processed_count=len(candidates),
            succeeded_count=bounded.metrics.legitimate_unavailable_count,
            skipped_count=bounded.metrics.unresolved_unavailable_count,
            retry_count=bounded.metrics.retry_count,
            provider_failure_count=bounded.metrics.provider_failure_count,
            metadata={"metrics": bounded.metrics.to_dict()},
        )
        return bounded

    def _refresh_tracking_universe_with_retry(
        self,
        *,
        now: datetime,
        eligible_instrument_ids: Collection[Any],
    ) -> int:
        repository = LiveRepository(self.session, self.config)
        try:
            return repository.refresh_tracking_universe(
                now=now,
                eligible_instrument_ids=eligible_instrument_ids,
            )
        except DBAPIError:
            # A provider-sized post-close run can outlive a database backend
            # connection. Roll back the invalid transaction and let
            # pool_pre_ping acquire a fresh connection for the bounded retry.
            self.session.rollback()
            return repository.refresh_tracking_universe(
                now=now,
                eligible_instrument_ids=eligible_instrument_ids,
            )

    def _finish_with_retry(self, run_id: Any, **values: Any) -> None:
        try:
            self._finish(run_id, **values)
        except DBAPIError:
            self.session.rollback()
            self._finish(run_id, **values)

    def _mark_finalization_failure(self, run_id: Any, exc: Exception) -> None:
        """Best-effort terminal audit write after an unhandled finalization error."""

        try:
            self.session.rollback()
            bind = self.session.get_bind()
        except Exception:
            return

        try:
            with Session(bind=bind, expire_on_commit=False) as recovery_session:
                run = recovery_session.get(LiveCollectorRun, run_id)
                if run is None or run.status != "RUNNING":
                    return
                now = self._now()
                run.status = "FAILED"
                run.freshness_state = "PARTIAL"
                run.provider_status = "ERROR"
                run.failure_code = "POST_CLOSE_FINALIZATION_FAILED"
                run.failure_message = f"{type(exc).__name__}: {str(exc)[:500]}"
                metadata = dict(run.metadata_payload or {})
                metadata["finalizationError"] = {
                    "status": "FAILED",
                    "errorCode": "POST_CLOSE_FINALIZATION_FAILED",
                    "exceptionType": type(exc).__name__,
                }
                run.metadata_payload = metadata
                run.completed_at = now
                run.heartbeat_at = now
                run.updated_at = now
                recovery_session.commit()
        except Exception:
            # If the database itself is unavailable, preserve the original
            # exception. The next process can recover from persisted attempts.
            return

    def _finalize_targeted_run(
        self,
        *,
        run_id: Any,
        local_date: date,
        requested_count: int,
        success_count: int,
        failure_count: int,
        skipped_count: int,
        retry_count: int,
        point_count: int,
        failure_codes: Collection[str],
    ) -> PostCloseRunResult:
        """Finalize a bounded symbol capture without full-market promotion."""

        final_failure_codes = tuple(sorted(set(failure_codes)))
        if not final_failure_codes and skipped_count:
            final_failure_codes = ("MISSING_MARKET_DATA",)
        status = "PARTIAL" if failure_count or skipped_count else "SUCCESS"
        snapshot_result = {
            "snapshotDate": local_date.isoformat(),
            "topicCount": 0,
            "status": "NOT_RUN_TARGETED",
        }
        self._ensure_completed_checkpoint(
            run_id=run_id,
            batch_key="FINAL_PUBLICATION",
            metadata={
                "outcome": "TARGETED_NOT_APPLICABLE",
                "publication": "NOT_RUN",
            },
        )
        self._finish_with_retry(
            run_id,
            status=status,
            success_count=success_count,
            failure_count=failure_count,
            skipped_count=skipped_count,
            retry_count=retry_count,
            point_count=point_count,
            failure_codes=final_failure_codes,
            snapshot_result=snapshot_result,
            reconciliation=None,
            now=self._now(),
        )
        self._checkpoint_event(
            run_id=run_id,
            batch_key="COMPLETION",
            status="COMPLETED" if status == "SUCCESS" else "PARTIAL",
            metadata={"runStatus": status, "formalReadback": "NOT_APPLICABLE"},
        )
        return PostCloseRunResult(
            str(run_id),
            status,
            requested_count,
            success_count,
            failure_count,
            skipped_count,
            retry_count,
            point_count,
            0,
            final_failure_codes,
            snapshot_result["topicCount"],
            snapshot_result["status"],
            local_date.isoformat(),
            False,
            getattr(self, "_status_resolution_metrics", StatusResolutionMetrics()).to_dict(),
        )

    def _finalize_collected_run(
        self,
        *,
        run_id: Any,
        local_date: date,
        eligible_instrument_ids: Collection[Any],
        success_count: int,
        failure_count: int,
        skipped_count: int,
        retry_count: int,
        point_count: int,
        failure_codes: Collection[str],
    ) -> PostCloseRunResult:
        try:
            reconciliation = reconcile_daily_market(
                self.session,
                local_date,
                expected_instrument_ids=eligible_instrument_ids,
                status_resolutions=getattr(self, "_status_resolution_by_instrument_id", {}),
            )
            if failure_count or skipped_count:
                status = "PARTIAL" if success_count else "FAILED"
            else:
                status = "SUCCESS"
            if status == "SUCCESS" and not reconciliation.downstream_ready:
                status = "PARTIAL"

            tracking_count = self._refresh_tracking_universe_with_retry(
                now=self._now(),
                eligible_instrument_ids=eligible_instrument_ids,
            )
            snapshot_result: dict[str, Any]
            formal_readback = self._formal_publication_readback(
                local_date,
                run_id=run_id,
                execution_scope=getattr(
                    self, "_active_execution_scope", NORMAL_CURRENT_DAY
                ),
            )
            formal_phase_key = "A9_B2_FORMAL_PROCESSING"
            formal_phase = self._latest_checkpoint(run_id, formal_phase_key)
            market_facts_key = "FORMAL_MARKET_FACTS:OFFICIAL"
            market_facts_phase = self._latest_checkpoint(run_id, market_facts_key)
            if (
                reconciliation.downstream_ready
                and formal_phase is not None
                and formal_phase.status in {"IN_PROGRESS", "COMPLETED"}
                and formal_readback["status"] == "PASS"
            ):
                # Publication already committed before a prior worker stopped.
                # Read it back and converge without invoking the writers again.
                run_metadata = self.session.get(LiveCollectorRun, run_id)
                snapshot_result = dict(
                    (run_metadata.metadata_payload if run_metadata else {}).get("topicSnapshot", {})
                )
                snapshot_result.setdefault("snapshotDate", local_date.isoformat())
                snapshot_result.setdefault(
                    "topicCount", formal_readback["topicSnapshot"]["rowCount"]
                )
                snapshot_result.setdefault("status", "SUCCESS")
                snapshot_result.setdefault(
                    "formalTopicDailyState",
                    {"status": "SUCCESS", "statusReason": "READBACK_REUSED"},
                )
                snapshot_result["formalTopicSnapshotReadback"] = formal_readback["topicSnapshot"]
                snapshot_result["formalStrengthReadback"] = formal_readback.get(
                    "formalStrength", {"status": "NOT_CHECKED"}
                )
                snapshot_result["formalLifecycleReadback"] = formal_readback.get(
                    "formalLifecycle", {"status": "NOT_CHECKED"}
                )
                snapshot_result["formalPublicationReadback"] = formal_readback
                if market_facts_phase is None or market_facts_phase.status != "COMPLETED":
                    self._checkpoint_event(
                        run_id=run_id,
                        batch_key=market_facts_key,
                        batch_number=150,
                        status="COMPLETED",
                        metadata={
                            "publicationAuthority": "topicpilot.market_institutional_flow_daily",
                            "readback": formal_readback.get("institutionalFlow"),
                            "reconciledFromCommittedOutputs": True,
                        },
                    )
            else:
                market_index_facts = fetch_official_market_indexes(
                    target_date=local_date,
                    retrieved_at=self._now(),
                    as_of=self._now(),
                    transport=_official_transport,
                )
                market_aggregate_facts = fetch_official_market_aggregates(
                    target_date=local_date,
                    retrieved_at=self._now(),
                    as_of=self._now(),
                    transport=_official_transport,
                )
                market_institutional_flow_facts = fetch_official_market_institutional_flows(
                    target_date=local_date,
                    retrieved_at=self._now(),
                    as_of=self._now(),
                    transport=_official_transport,
                )
                self._checkpoint_event(
                    run_id=run_id,
                    batch_key=market_facts_key,
                    batch_number=150,
                    status="IN_PROGRESS",
                    metadata={
                        "sessionDate": local_date,
                        "publicationAuthority": "topicpilot.market_institutional_flow_daily",
                        "sourceIdentities": sorted(
                            {
                                str(getattr(fact, "source_identity", ""))
                                for fact in market_institutional_flow_facts
                            }
                        ),
                    },
                )
                institutional_flow_persistence = self._persist_official_institutional_flow(
                    tuple(market_institutional_flow_facts),
                    existing_readback=formal_readback.get("institutionalFlow"),
                )
                if reconciliation.downstream_ready:
                    self._checkpoint_event(
                        run_id=run_id,
                        batch_key=formal_phase_key,
                        status="IN_PROGRESS",
                        metadata={
                            "sessionDate": local_date,
                            "a9B2Boundary": "PRESERVED",
                            "publicationAuthority": "topicpilot.topic_snapshots",
                        },
                    )
                    snapshot_result = self._run_snapshot(
                        local_date,
                        eligible_instrument_ids=eligible_instrument_ids,
                        source_run_id=str(run_id),
                        market_index_facts=market_index_facts,
                        market_aggregate_facts=market_aggregate_facts,
                        market_institutional_flow_facts=(),
                        execution_scope=getattr(
                            self, "_active_execution_scope", NORMAL_CURRENT_DAY
                        ),
                    )
                    snapshot_result["marketInstitutionalFlow"] = institutional_flow_persistence
                else:
                    snapshot_result = self._publish_market_facts_only(
                        local_date,
                        source_run_id=str(run_id),
                        market_index_facts=market_index_facts,
                        market_aggregate_facts=market_aggregate_facts,
                        market_institutional_flow_facts=market_institutional_flow_facts,
                        market_institutional_flow_result=institutional_flow_persistence,
                        eligible_instrument_ids=eligible_instrument_ids,
                        execution_scope=getattr(
                            self, "_active_execution_scope", NORMAL_CURRENT_DAY
                        ),
                    )
                formal_readback = self._formal_publication_readback(
                    local_date,
                    run_id=run_id,
                    execution_scope=getattr(
                        self, "_active_execution_scope", NORMAL_CURRENT_DAY
                    ),
                )
                snapshot_result["formalPublicationReadback"] = formal_readback

                flow_readback = formal_readback.get("institutionalFlow", {})
                self._checkpoint_event(
                    run_id=run_id,
                    batch_key=market_facts_key,
                    batch_number=150,
                    status=("COMPLETED" if flow_readback.get("status") == "PASS" else "FAILED"),
                    failed_count=0 if flow_readback.get("status") == "PASS" else 1,
                    metadata={
                        "publicationAuthority": "topicpilot.market_institutional_flow_daily",
                        "readback": flow_readback,
                        "marketFactsPublication": snapshot_result.get("marketFactsPublication"),
                        **_readback_failure_metadata(
                            formal_readback=formal_readback,
                            market_facts_publication=snapshot_result.get("marketFactsPublication"),
                        ),
                    },
                )
            if "formalPublicationReadback" not in snapshot_result:
                snapshot_result["formalPublicationReadback"] = formal_readback
            formal_ready = self._formal_snapshot_ready(snapshot_result)
            formal_publication_ready = formal_readback.get("status") == "PASS"
            if formal_ready and formal_publication_ready:
                self._ensure_completed_checkpoint(
                    run_id=run_id,
                    batch_key="A9_B2_FORMAL_PROCESSING",
                    metadata={
                        "readback": formal_readback,
                        "formalStrength": formal_readback.get("formalStrength"),
                        "formalLifecycle": formal_readback.get("formalLifecycle"),
                        "semanticsChanged": False,
                    },
                )
                self._ensure_completed_checkpoint(
                    run_id=run_id,
                    batch_key="FINAL_PUBLICATION",
                    metadata={
                        "formalPublication": formal_readback,
                        "formalStrength": formal_readback.get("formalStrength"),
                        "formalLifecycle": formal_readback.get("formalLifecycle"),
                        "homePublication": formal_readback["homePublication"],
                    },
                )
            else:
                if formal_ready:
                    self._ensure_completed_checkpoint(
                        run_id=run_id,
                        batch_key="A9_B2_FORMAL_PROCESSING",
                        metadata={
                            "readback": formal_readback,
                            "formalStrength": formal_readback.get("formalStrength"),
                            "formalLifecycle": formal_readback.get("formalLifecycle"),
                            "semanticsChanged": False,
                        },
                    )
                self._checkpoint_event(
                    run_id=run_id,
                    batch_key="FINAL_PUBLICATION",
                    status="FAILED",
                    failed_count=1,
                    metadata={
                        "errorCode": (
                            "CHECKPOINT_PUBLICATION_MISMATCH"
                            if formal_phase is not None and formal_phase.status == "COMPLETED"
                            else "FORMAL_PUBLICATION_READBACK_NOT_READY"
                            if formal_ready
                            else "FORMAL_TOPIC_SNAPSHOT_NOT_READY"
                        ),
                        "readback": formal_readback,
                        **_readback_failure_metadata(
                            formal_readback=formal_readback,
                            market_facts_publication=snapshot_result.get("marketFactsPublication"),
                        ),
                    },
                )
            final_failure_codes = tuple(sorted(set(failure_codes)))
            if not (formal_ready and formal_publication_ready):
                if status == "SUCCESS":
                    status = "PARTIAL"
                final_failure_codes = tuple(
                    sorted(
                        {
                            *final_failure_codes,
                            (
                                "FORMAL_TOPIC_SNAPSHOT_NOT_READY"
                                if not formal_ready
                                else "FORMAL_PUBLICATION_READBACK_NOT_READY"
                            ),
                        }
                    )
                )
            final_failure_codes = final_failure_codes or reconciliation.reason_codes
            if not final_failure_codes and skipped_count:
                final_failure_codes = ("NO_TRADING_DAY_DATA",)
            self._finish_with_retry(
                run_id,
                status=status,
                success_count=success_count,
                failure_count=failure_count,
                skipped_count=skipped_count,
                retry_count=retry_count,
                point_count=point_count,
                failure_codes=final_failure_codes,
                snapshot_result=snapshot_result,
                reconciliation=reconciliation,
                now=self._now(),
            )
            if status in {"SUCCESS", "PARTIAL", "FAILED"}:
                self._checkpoint_event(
                    run_id=run_id,
                    batch_key="COMPLETION",
                    status="COMPLETED" if status == "SUCCESS" else "PARTIAL",
                    metadata={
                        "runStatus": status,
                        "formalReadback": formal_readback,
                        "failureCodes": final_failure_codes,
                    },
                )
        except Exception as exc:
            self._mark_finalization_failure(run_id, exc)
            raise

        return PostCloseRunResult(
            str(run_id),
            status,
            len(eligible_instrument_ids),
            success_count,
            failure_count,
            skipped_count,
            retry_count,
            point_count,
            tracking_count,
            final_failure_codes,
            snapshot_result.get("topicCount", 0),
            snapshot_result.get("status", "FAILED"),
            local_date.isoformat(),
            False,
            getattr(self, "_status_resolution_metrics", StatusResolutionMetrics()).to_dict(),
        )

    def _publish_market_facts_only(
        self,
        snapshot_date: date,
        *,
        source_run_id: str,
        market_index_facts: Collection[Any],
        market_aggregate_facts: Collection[Any],
        market_institutional_flow_facts: Collection[Any],
        market_institutional_flow_result: Mapping[str, Any] | None = None,
        execution_scope: str | None = None,
        eligible_instrument_ids: Collection[Any] | None = None,
    ) -> dict[str, Any]:
        """Publish formal exchange-level facts without bypassing stock gates.

        A missing stock bar blocks stock-dependent topic work, but it must not
        suppress independently sourced whole-market index, breadth, turnover,
        or institutional facts.  Each of those inputs remains typed and
        fail-closed, so an unavailable provider fact cannot become a zero or a
        single-market Taiwan total.
        """

        result: dict[str, Any] = {
            "snapshotDate": snapshot_date.isoformat(),
            "topicCount": 0,
            "status": "BLOCKED_DAILY_MARKET_NOT_READY",
            "marketFactsOnly": True,
        }
        try:
            if market_institutional_flow_result is not None:
                result["marketInstitutionalFlow"] = dict(market_institutional_flow_result)
            elif market_institutional_flow_facts:
                try:
                    result["marketInstitutionalFlow"] = persist_market_institutional_flows(
                        self.session,
                        tuple(market_institutional_flow_facts),
                        ingested_at=self._now(),
                    )
                except SQLAlchemyError as exc:
                    self.session.rollback()
                    result["marketInstitutionalFlow"] = {
                        "status": "PERSISTENCE_UNAVAILABLE",
                        "error": type(exc).__name__,
                    }
            resolved_scope = execution_scope or getattr(
                self, "_active_execution_scope", NORMAL_CURRENT_DAY
            )
            if resolved_scope == HISTORY_RECOVERY:
                result["homePublication"] = {
                    "status": "FORBIDDEN",
                    "reasonCode": "HISTORY_RECOVERY_HOME_PUBLICATION_FORBIDDEN",
                    "publicationScope": HISTORY_RECOVERY,
                }
            elif snapshot_date != getattr(self, "_active_run_date", snapshot_date):
                result["homePublication"] = {
                    "status": "BLOCKED",
                    "reasonCode": "NORMAL_CURRENT_DAY_HOME_DATE_MISMATCH",
                    "publicationScope": NORMAL_CURRENT_DAY,
                }
            else:
                result["homePublication"] = materialize_home_v2(
                    self.session,
                    trading_date=snapshot_date,
                    source_run_id=source_run_id,
                    expected_instrument_ids=eligible_instrument_ids,
                    market_index_facts=tuple(market_index_facts),
                    market_aggregate_facts=tuple(market_aggregate_facts),
                )
            result["marketFactsPublication"] = {
                "status": "SUCCESS",
                "institutionalFlow": result.get("marketInstitutionalFlow"),
            }
        except Exception as exc:
            self.session.rollback()
            result["homePublication"] = {
                "status": "HOME_PUBLICATION_UNAVAILABLE",
                "error": type(exc).__name__,
            }
            result["marketFactsPublication"] = {
                "status": "UNAVAILABLE",
                "error": type(exc).__name__,
            }
        return result

    def _persist_official_institutional_flow(
        self,
        facts: Collection[Any],
        *,
        existing_readback: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        """Commit official flow facts once before A9/B2 processing."""

        if existing_readback and existing_readback.get("status") == "PASS":
            return {
                "status": "IDEMPOTENT_READBACK",
                "persisted": 0,
                "available": len(existing_readback.get("availableMarkets", ())),
            }
        if not facts:
            return {"status": "NOT_AVAILABLE", "persisted": 0, "available": 0}
        try:
            result = persist_market_institutional_flows(
                self.session,
                tuple(facts),
                ingested_at=self._now(),
            )
            self.session.commit()
            return dict(result)
        except SQLAlchemyError as exc:
            with suppress(Exception):
                self.session.rollback()
            return {
                "status": "PERSISTENCE_UNAVAILABLE",
                "persisted": 0,
                "available": 0,
                "error": type(exc).__name__,
            }
        except Exception as exc:
            with suppress(Exception):
                self.session.rollback()
            return {
                "status": "PERSISTENCE_UNAVAILABLE",
                "persisted": 0,
                "available": 0,
                "error": type(exc).__name__,
            }

    @staticmethod
    def _formal_snapshot_ready(snapshot_result: Mapping[str, Any]) -> bool:
        formal_state = snapshot_result.get("formalTopicDailyState") or {}
        formal_readback = snapshot_result.get("formalTopicSnapshotReadback") or {}
        return (
            snapshot_result.get("status") == "SUCCESS"
            and formal_state.get("status") == "SUCCESS"
            and formal_readback.get("status") == "PASS"
        )

    @staticmethod
    def _formal_strength_ready(snapshot_result: Mapping[str, Any]) -> bool:
        return (snapshot_result.get("formalStrengthReadback") or {}).get("status") == "PASS"

    def _formal_snapshot_readback(self, snapshot_date: date) -> dict[str, Any]:
        rows = self.session.scalars(
            select(TopicSnapshot).where(
                TopicSnapshot.snapshot_date == snapshot_date,
                TopicSnapshot.publication_mode == "FORMAL",
                TopicSnapshot.membership_mode == "PIT_FORMAL",
                TopicSnapshot.trading_day_state == "TRADING",
                TopicSnapshot.generated_state == "GENERATED",
                TopicSnapshot.finality_state == "FINAL",
                TopicSnapshot.publication_state == "PUBLISHED",
                TopicSnapshot.superseded_by_snapshot_id.is_(None),
            )
        ).all()
        topic_ids = [row.topic_id for row in rows]
        valid = (
            bool(rows)
            and len(topic_ids) == len(set(topic_ids))
            and all(
                row.membership_snapshot_id
                and row.membership_snapshot_hash
                and row.relation_version
                and row.source_artifact_hash
                and row.lineage_hash
                for row in rows
            )
        )
        return {
            "status": "PASS" if valid else "FAIL",
            "snapshotDate": snapshot_date.isoformat(),
            "rowCount": len(rows),
            "distinctTopicCount": len(set(topic_ids)),
            "authority": "topicpilot.topic_snapshots",
            "publicationMode": "FORMAL",
            "publicationState": "PUBLISHED",
            "membershipMode": "PIT_FORMAL",
        }

    def _institutional_flow_readback(self, snapshot_date: date) -> dict[str, Any]:
        """Read both official exchange rows before allowing terminal success."""

        expected_markets = ("TPE", "TWO")
        expected_sources = {
            "TPE": "TWSE_BFI82U",
            "TWO": "TPEX_INSTI_SUMMARY",
        }
        try:
            rows = list(
                self.session.execute(
                    text(
                        """
                        SELECT market, trading_date, availability, source_identity
                        FROM topicpilot.market_institutional_flow_daily
                        WHERE trading_date = :trading_date
                          AND market IN ('TPE', 'TWO')
                        ORDER BY market, source_as_of DESC NULLS LAST,
                                 published_at DESC NULLS LAST, id DESC
                        """
                    ),
                    {"trading_date": snapshot_date},
                )
                .mappings()
                .all()
            )
        except Exception as exc:
            with suppress(Exception):
                self.session.rollback()
            return {
                "status": "FAIL",
                "tradingDate": snapshot_date.isoformat(),
                "expectedMarkets": list(expected_markets),
                "availableMarkets": [],
                "authority": "topicpilot.market_institutional_flow_daily",
                "reasonCode": "INSTITUTIONAL_FLOW_READBACK_UNAVAILABLE",
                "error": type(exc).__name__,
            }

        selected: dict[str, Mapping[str, Any]] = {}
        for market in expected_markets:
            market_rows = [row for row in rows if str(row.get("market")) == market]
            selected[market] = next(
                (
                    row
                    for row in market_rows
                    if str(row.get("source_identity")) == expected_sources[market]
                ),
                market_rows[0] if market_rows else {},
            )

        def row_date(value: Any) -> str:
            if isinstance(value, datetime):
                return value.date().isoformat()
            if isinstance(value, date):
                return value.isoformat()
            return str(value or "")[:10]

        valid = all(
            selected[market]
            and row_date(selected[market].get("trading_date")) == snapshot_date.isoformat()
            and selected[market].get("availability") == "AVAILABLE"
            and selected[market].get("source_identity") == expected_sources[market]
            for market in expected_markets
        )
        available_markets = [
            market
            for market in expected_markets
            if selected[market].get("availability") == "AVAILABLE"
        ]
        return {
            "status": "PASS" if valid else "FAIL",
            "tradingDate": snapshot_date.isoformat(),
            "expectedMarkets": list(expected_markets),
            "availableMarkets": available_markets,
            "markets": [
                {
                    "market": market,
                    "tradingDate": row_date(selected[market].get("trading_date")),
                    "availability": selected[market].get("availability"),
                    "sourceIdentity": selected[market].get("source_identity"),
                }
                for market in expected_markets
            ],
            "authority": "topicpilot.market_institutional_flow_daily",
            "reasonCode": None if valid else "WHOLE_MARKET_INSTITUTIONAL_FLOW_NOT_READY",
        }

    def _formal_publication_readback(
        self,
        snapshot_date: date,
        *,
        run_id: Any | None = None,
        execution_scope: str | None = None,
    ) -> dict[str, Any]:
        """Read the authoritative outputs used by the completion gate."""

        topic = self._formal_snapshot_readback(snapshot_date)
        resolved_scope = execution_scope or getattr(
            self, "_active_execution_scope", NORMAL_CURRENT_DAY
        )
        history_recovery = resolved_scope == HISTORY_RECOVERY
        home = None
        if run_id is not None and not history_recovery:
            home = self.session.scalar(
                select(HomePublication)
                .where(
                    HomePublication.trading_date == snapshot_date,
                    HomePublication.source_run_id == str(run_id),
                    HomePublication.publication_state == "PUBLISHED",
                )
                .order_by(HomePublication.generated_at.desc(), HomePublication.id.desc())
                .limit(1)
            )
        institutional_flow = self._institutional_flow_readback(snapshot_date)
        home_status = (
            "FORBIDDEN"
            if history_recovery
            else
            "PASS"
            if home is not None and home.publication_state == "PUBLISHED"
            else "NOT_FOUND"
            if home is None
            else "NOT_PUBLISHED"
        )
        strength = self._formal_strength_readback(snapshot_date)
        lifecycle = self._formal_lifecycle_readback(snapshot_date)
        base_ready = (
            topic["status"] == "PASS"
            and (history_recovery or home_status == "PASS")
            and institutional_flow["status"] == "PASS"
        )
        return {
            "status": (
                "PASS"
                if base_ready
                and strength["status"] in {"PASS", "NOT_CHECKED"}
                and lifecycle["status"] in {"PASS", "NOT_CHECKED"}
                else "PARTIAL"
                if base_ready
                else "FAIL"
            ),
            "topicSnapshot": topic,
            "homePublication": {
                "status": home_status,
                "publicationId": str(home.id) if home is not None else None,
                "publicationState": home.publication_state if home is not None else None,
                "authority": "topicpilot.home_publications",
                "publicationScope": resolved_scope,
                "reasonCode": (
                    "HISTORY_RECOVERY_HOME_PUBLICATION_FORBIDDEN"
                    if history_recovery
                    else None
                ),
            },
            "institutionalFlow": institutional_flow,
            "formalStrength": strength,
            "formalLifecycle": lifecycle,
        }

    def _formal_strength_readback(self, snapshot_date: date) -> dict[str, Any]:
        try:
            rows = (
                self.session.execute(
                    text(
                        """
                    SELECT r.publication_status, r.evaluation_status
                    FROM topicpilot.topic_score_formal_results r
                    WHERE r.evaluation_date = :snapshot_date
                      AND r.publication_mode = 'FORMAL'
                      AND r.contract_version = 'topic-strength-lifecycle.formal.v1'
                      AND NOT EXISTS (
                          SELECT 1 FROM topicpilot.topic_score_formal_results successor
                          WHERE successor.supersedes_decision_id = r.id
                      )
                    """
                    ),
                    {"snapshot_date": snapshot_date},
                )
                .mappings()
                .all()
            )
            if rows and "publication_status" not in rows[0]:
                return {"status": "NOT_CHECKED", "authority": "FORMAL_STRENGTH"}
        except SQLAlchemyError as exc:
            return {
                "status": "FAIL",
                "authority": "FORMAL_STRENGTH",
                "reasonCode": "FORMAL_STRENGTH_READBACK_UNAVAILABLE",
                "error": type(exc).__name__,
            }
        except Exception:
            return {"status": "NOT_CHECKED", "authority": "FORMAL_STRENGTH"}
        try:
            expected_scope = self.session.execute(
                text(
                    """
                    SELECT COUNT(DISTINCT t.id)
                    FROM topicpilot.topics t
                    JOIN topicpilot.topic_hierarchy h ON h.child_topic_id = t.id
                    WHERE h.valid_from <= :snapshot_date
                      AND (h.valid_to IS NULL OR h.valid_to >= :snapshot_date)
                      AND t.status NOT IN ('DISABLED', 'RETIRED')
                      AND (t.valid_from IS NULL OR t.valid_from <= :snapshot_date)
                      AND (t.valid_to IS NULL OR t.valid_to >= :snapshot_date)
                    """
                ),
                {"snapshot_date": snapshot_date},
            ).scalar()
        except SQLAlchemyError as exc:
            return {
                "status": "FAIL",
                "authority": "FORMAL_STRENGTH",
                "reasonCode": "FORMAL_STRENGTH_SCOPE_READBACK_UNAVAILABLE",
                "error": type(exc).__name__,
            }
        except Exception:
            return {"status": "NOT_CHECKED", "authority": "FORMAL_STRENGTH"}
        published = sum(row["publication_status"] == "PUBLISHED" for row in rows)
        return {
            "status": (
                "PASS"
                if rows and expected_scope == len(rows) and published == len(rows)
                else "PARTIAL"
                if published
                else "FAIL"
            ),
            "rowCount": len(rows),
            "expectedScopeCount": expected_scope,
            "publishedRowCount": published,
            "authority": "topicpilot.topic_score_formal_results",
        }

    def _formal_lifecycle_readback(self, snapshot_date: date) -> dict[str, Any]:
        try:
            rows = (
                self.session.execute(
                    text(
                        """
                    SELECT r.publication_status
                    FROM topicpilot.topic_lifecycle_formal_results r
                    WHERE r.evaluation_date = :snapshot_date
                      AND r.evaluation_mode = 'FORMAL'
                      AND NOT EXISTS (
                          SELECT 1 FROM topicpilot.topic_lifecycle_formal_results successor
                          WHERE successor.supersedes_decision_id = r.id
                      )
                    """
                    ),
                    {"snapshot_date": snapshot_date},
                )
                .mappings()
                .all()
            )
            if rows and "publication_status" not in rows[0]:
                return {"status": "NOT_CHECKED", "authority": "FORMAL_LIFECYCLE"}
        except SQLAlchemyError as exc:
            return {
                "status": "FAIL",
                "authority": "FORMAL_LIFECYCLE",
                "reasonCode": "FORMAL_LIFECYCLE_READBACK_UNAVAILABLE",
                "error": type(exc).__name__,
            }
        except Exception:
            return {"status": "NOT_CHECKED", "authority": "FORMAL_LIFECYCLE"}
        try:
            expected_scope = self.session.execute(
                text(
                    """
                    SELECT COUNT(DISTINCT t.id)
                    FROM topicpilot.topics t
                    JOIN topicpilot.topic_hierarchy h ON h.child_topic_id = t.id
                    WHERE h.valid_from <= :snapshot_date
                      AND (h.valid_to IS NULL OR h.valid_to >= :snapshot_date)
                      AND t.status NOT IN ('DISABLED', 'RETIRED')
                      AND (t.valid_from IS NULL OR t.valid_from <= :snapshot_date)
                      AND (t.valid_to IS NULL OR t.valid_to >= :snapshot_date)
                    """
                ),
                {"snapshot_date": snapshot_date},
            ).scalar()
        except SQLAlchemyError as exc:
            return {
                "status": "FAIL",
                "authority": "FORMAL_LIFECYCLE",
                "reasonCode": "FORMAL_LIFECYCLE_SCOPE_READBACK_UNAVAILABLE",
                "error": type(exc).__name__,
            }
        except Exception:
            return {"status": "NOT_CHECKED", "authority": "FORMAL_LIFECYCLE"}
        published = sum(row["publication_status"] == "PUBLISHED" for row in rows)
        return {
            "status": (
                "PASS"
                if rows and expected_scope == len(rows) and published == len(rows)
                else "PARTIAL"
                if published
                else "FAIL"
            ),
            "rowCount": len(rows),
            "expectedScopeCount": expected_scope,
            "publishedRowCount": published,
            "authority": "topicpilot.topic_lifecycle_formal_results",
        }

    def _run_snapshot(
        self,
        snapshot_date: date,
        *,
        market_closed: bool = False,
        eligible_instrument_ids: Collection[Any] | None = None,
        source_run_id: str | None = None,
        market_index_facts: Collection[Any] = (),
        market_aggregate_facts: Collection[Any] = (),
        market_institutional_flow_facts: Collection[Any] = (),
        execution_scope: str | None = None,
    ) -> dict[str, Any]:
        try:
            result = TopicSnapshotEngine(self.session).run_once(
                snapshot_date=snapshot_date,
                market_closed=market_closed,
                eligible_instrument_ids=eligible_instrument_ids,
            )
            if result.get("status") == "SUCCESS" and not market_closed:
                try:
                    formal_state = materialize_bounded_formal_dates(
                        self.session,
                        dates=(snapshot_date,),
                    )
                    result["formalTopicDailyState"] = {
                        "status": "SUCCESS",
                        "rowsBefore": formal_state["rowsBefore"],
                        "rowsAfter": formal_state["rowsAfter"],
                        "writes": formal_state["writes"],
                        "preBoundaryBackfill": formal_state["preBoundaryBackfill"],
                    }
                    result["formalTopicSnapshotReadback"] = self._formal_snapshot_readback(
                        snapshot_date
                    )
                except Exception as exc:
                    # The canonical snapshot is retained, but the formal
                    # publication chain is explicitly unavailable.  A
                    # missing authority/migration or transient failure must
                    # never be replaced by shadow output.
                    self.session.rollback()
                    result["formalTopicDailyState"] = {
                        "status": "FORMAL_STATE_UNAVAILABLE",
                        "error": type(exc).__name__,
                    }
                if result["formalTopicDailyState"]["status"] == "SUCCESS":
                    try:
                        strength_run = FormalStrengthPublisher(self.session).run_once(
                            evaluation_date=snapshot_date,
                            market_index_facts=tuple(market_index_facts),
                        )
                        result["formalStrength"] = strength_run.as_dict()
                        result["formalStrengthReadback"] = self._formal_strength_readback(
                            snapshot_date
                        )
                    except Exception as exc:
                        # Strength and Lifecycle are independent publication
                        # lanes.  Keep this failure local so Lifecycle still
                        # gets a chance to publish from its own formal facts.
                        self.session.rollback()
                        result["formalStrength"] = {
                            "status": "FAIL_CLOSED",
                            "unavailableRows": 0,
                            "error": type(exc).__name__,
                        }
                        result["formalStrengthReadback"] = self._formal_strength_readback(
                            snapshot_date
                        )
                    try:
                        lifecycle_run = FormalLifecyclePublisher(self.session).run_once(
                            evaluation_date=snapshot_date,
                            market_index_facts=tuple(market_index_facts),
                        )
                        result["lifecycle"] = lifecycle_run.as_dict()
                        result["formalLifecycle"] = result["lifecycle"]
                        result["formalLifecycleReadback"] = self._formal_lifecycle_readback(
                            snapshot_date
                        )
                    except Exception as exc:
                        # Lifecycle is independently fail-closed; a Strength
                        # error must not be allowed to fabricate or suppress
                        # its audit row.
                        self.session.rollback()
                        result["lifecycle"] = {
                            "status": "FAIL_CLOSED",
                            "error": type(exc).__name__,
                        }
                        result["formalLifecycle"] = result["lifecycle"]
                        result["formalLifecycleReadback"] = self._formal_lifecycle_readback(
                            snapshot_date
                        )
                else:
                    result["formalStrength"] = {"status": "WAITING_FOR_FORMAL_SNAPSHOT"}
                    result["formalStrengthReadback"] = {"status": "FAIL"}
                    result["lifecycle"] = {"status": "WAITING_FOR_FORMAL_SNAPSHOT"}
                    result["formalLifecycleReadback"] = {"status": "FAIL"}
                resolved_scope = execution_scope or getattr(
                    self, "_active_execution_scope", NORMAL_CURRENT_DAY
                )
                if resolved_scope == HISTORY_RECOVERY:
                    result["homePublication"] = {
                        "status": "FORBIDDEN",
                        "reasonCode": "HISTORY_RECOVERY_HOME_PUBLICATION_FORBIDDEN",
                        "publicationScope": HISTORY_RECOVERY,
                    }
                elif snapshot_date != getattr(self, "_active_run_date", snapshot_date):
                    result["homePublication"] = {
                        "status": "BLOCKED",
                        "reasonCode": "NORMAL_CURRENT_DAY_HOME_DATE_MISMATCH",
                        "publicationScope": NORMAL_CURRENT_DAY,
                    }
                else:
                    try:
                        result["homePublication"] = materialize_home_v2(
                            self.session,
                            trading_date=snapshot_date,
                            source_run_id=source_run_id,
                            expected_instrument_ids=eligible_instrument_ids,
                            market_index_facts=tuple(market_index_facts),
                            market_aggregate_facts=tuple(market_aggregate_facts),
                        )
                    except Exception as exc:
                        # Home publication has its own typed gate.  A Home
                        # persistence failure must not rewrite a successfully
                        # materialized formal topic state as unavailable.
                        self.session.rollback()
                        result["homePublication"] = {
                            "status": "HOME_PUBLICATION_UNAVAILABLE",
                            "error": type(exc).__name__,
                        }
            elif market_closed:
                result["lifecycle"] = {"status": "MARKET_CLOSED"}
            return result
        except Exception as exc:
            self.session.rollback()
            return {
                "snapshotDate": snapshot_date.isoformat(),
                "topicCount": 0,
                "status": "FAILED",
                "error": type(exc).__name__,
            }

    def _finish(
        self,
        run_id: Any,
        *,
        status: str,
        success_count: int,
        failure_count: int,
        skipped_count: int,
        retry_count: int,
        point_count: int,
        failure_codes: tuple[str, ...],
        snapshot_result: dict[str, Any] | None = None,
        reconciliation: DailyMarketReconciliation | None = None,
        now: datetime,
    ) -> None:
        run = self.session.get(LiveCollectorRun, run_id)
        if run is None:
            return
        run.status = status
        run.success_count = success_count
        run.failure_count = failure_count
        run.retry_count = retry_count
        run.latency_ms = max(0, int((now - run.started_at).total_seconds() * 1000))
        run.freshness_state = (
            "FRESH"
            if status == "SUCCESS"
            else "NOT_APPLICABLE"
            if status == "MARKET_CLOSED"
            else "PARTIAL"
        )
        run.provider_status = (
            "AVAILABLE"
            if status in {"SUCCESS", "PARTIAL"}
            else "NOT_CALLED"
            if status == "MARKET_CLOSED"
            else "ERROR"
        )
        run.failure_code = failure_codes[0] if failure_codes else None
        run.failure_message = ";".join(failure_codes) if failure_codes else None
        metadata = dict(run.metadata_payload or {})
        metadata.update(
            {
                "skippedCount": skipped_count,
                "providerPointCount": point_count,
                "failureCodes": list(failure_codes),
                "dailyMarketReconciliation": (
                    reconciliation.to_dict() if reconciliation else {"status": "NOT_RUN"}
                ),
                "downstreamReady": bool(reconciliation and reconciliation.downstream_ready),
                "topicSnapshot": snapshot_result or {"status": "NOT_RUN"},
                "statusResolutionMetrics": getattr(
                    self,
                    "_status_resolution_metrics",
                    StatusResolutionMetrics(),
                ).to_dict(),
            }
        )
        if reconciliation and reconciliation.downstream_ready:
            metadata.setdefault("dataReadyAt", now.isoformat())
        reconciliation_payload = metadata.get("dailyMarketReconciliation") or {}
        snapshot_payload = metadata.get("topicSnapshot") or {}
        formal_state = snapshot_payload.get("formalTopicDailyState") or {}
        formal_readback = snapshot_payload.get("formalTopicSnapshotReadback") or {}
        is_market_closed = status == "MARKET_CLOSED"
        execution_scope = _metadata_execution_scope(metadata)
        publication_readback = snapshot_payload.get("formalPublicationReadback") or {}
        formal_chain_ready = (
            self._formal_snapshot_ready(snapshot_payload)
            and publication_readback.get("status") == "PASS"
        )
        if formal_chain_ready:
            metadata.setdefault("formalPublicationAt", now.isoformat())
        if execution_scope == HISTORY_RECOVERY:
            metadata["forwardAutomation"] = {
                "status": "NOT_APPLICABLE",
                "reasonCode": "HISTORY_RECOVERY_IS_NOT_CURRENT_DAY_PUBLICATION",
            }
            metadata["historyRecovery"] = {
                "status": (
                    "SUCCESS"
                    if status == "SUCCESS" and formal_chain_ready
                    else "MARKET_CLOSED"
                    if status == "MARKET_CLOSED"
                    else "BLOCKED"
                ),
                "targetDate": reconciliation_payload.get("tradeDate"),
                "formalHistoryPublication": (
                    "NOT_RUN"
                    if is_market_closed
                    else "PASS"
                    if formal_chain_ready
                    else "FAIL"
                ),
                "homePublication": "FORBIDDEN",
                "homeWriteCount": 0,
                "currentDayPresentation": "FORBIDDEN",
            }
        else:
            metadata["forwardAutomation"] = {
                "status": (
                    "SUCCESS"
                    if status == "SUCCESS"
                    and reconciliation_payload.get("downstreamReady") is True
                    and formal_chain_ready
                    else "MARKET_CLOSED"
                    if status == "MARKET_CLOSED"
                    else "BLOCKED"
                ),
                "targetDate": reconciliation_payload.get("tradeDate"),
                "formalEodPublication": (
                    "NOT_RUN"
                    if is_market_closed
                    else "PASS"
                    if reconciliation_payload.get("downstreamReady") is True
                    else "NOT_RUN"
                ),
                "formalEodReadback": (
                    "NOT_RUN"
                    if is_market_closed
                    else "PASS"
                    if reconciliation_payload.get("downstreamReady") is True
                    else "FAIL"
                ),
                "formalTopicSnapshotPublication": (
                    "NOT_RUN"
                    if is_market_closed
                    else "PASS"
                    if formal_state.get("status") == "SUCCESS"
                    else "FAIL"
                ),
                "formalTopicSnapshotReadback": (
                    "NOT_RUN" if is_market_closed else formal_readback.get("status", "FAIL")
                ),
                "formalStrengthPublication": (
                    "NOT_RUN"
                    if is_market_closed
                    else (snapshot_payload.get("formalStrength") or {}).get(
                        "status", "NOT_AVAILABLE"
                    )
                ),
                "formalStrengthReadback": (
                    "NOT_RUN"
                    if is_market_closed
                    else (publication_readback.get("formalStrength") or {}).get(
                        "status", "FAIL"
                    )
                ),
                "formalLifecyclePublication": (
                    "NOT_RUN"
                    if is_market_closed
                    else (
                        snapshot_payload.get("formalLifecycle")
                        or snapshot_payload.get("lifecycle")
                        or {}
                    ).get("status", "NOT_AVAILABLE")
                ),
                "formalLifecycleReadback": (
                    "NOT_RUN"
                    if is_market_closed
                    else (publication_readback.get("formalLifecycle") or {}).get(
                        "status", "FAIL"
                    )
                ),
            }
        run.metadata_payload = _json_safe(metadata)
        run.completed_at = now
        run.heartbeat_at = now
        run.updated_at = now
        receipt = append_receipt_for_run(
            self.session,
            run,
            self.config,
            now=now,
            commit=False,
        )
        metadata = dict(run.metadata_payload or {})
        metadata["dailyFormalPublicationReceipt"] = {
            "receiptId": str(receipt.id),
            "receiptStatus": receipt.receipt_status,
            "receiptRevision": receipt.receipt_revision,
            "receiptHash": receipt.receipt_hash,
            "readbackStatus": receipt.formal_readback_state,
            "runtimeProvenanceStatus": (receipt.runtime_provenance or {}).get("status"),
        }
        run.metadata_payload = _json_safe(metadata)
        self.session.commit()


__all__ = [
    "PostClosePreconditionError",
    "PostCloseRunResult",
    "PostCloseUpdater",
    "expected_post_close_universe",
    "resolve_post_close_run_date",
]
