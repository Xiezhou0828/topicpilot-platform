"""One explicit Home-only completion after an Owner normal run collected all data.

This is not normal execution re-entry. It cannot create a collector run, ingest
prices, apply comparators, resolve trading status, or calculate Topic results.
The original OwnerNormalExecution one-shot/reentryAllowed=False contract remains
unchanged. A separate authorization is durably consumed before the Home writer.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select

from topicpilot_api.daily_market import read_daily_market_rows, reconcile_daily_market
from topicpilot_api.home_v2_publication import materialize_home_v2
from topicpilot_api.market_data.aggregate_contract import (
    TPEX_DAILY_AGGREGATE_SOURCE,
    TWSE_DAILY_AGGREGATE_SOURCE,
)
from topicpilot_api.market_data.index_contract import IndexDataStatus
from topicpilot_api.orm import HomePublication, LiveCollectorCheckpoint, LiveCollectorRun
from topicpilot_api.provider_preflight import load_g2_preflight_context

from .post_close import NORMAL_CURRENT_DAY, PostClosePreconditionError, PostCloseUpdater, _json_safe

TARGET = date(2026, 10, 2)
COMPLETION_KEY = "OWNER_HOME_ONLY_COMPLETION"
FAILURE = "FORMAL_PUBLICATION_READBACK_NOT_READY"


def evaluate_home_completion(run: Any, checkpoints: Sequence[Any]) -> dict[str, Any]:
    """Pure, fail-closed review of the original execution and immutable events."""
    reasons: list[str] = []
    metadata = (run.metadata_payload or {}) if run is not None else {}
    owner = metadata.get("ownerNormalExecution") or {}
    key = str(metadata.get("executionKey") or "")
    if (
        run is None
        or run.run_type != "POST_CLOSE"
        or run.status != "PARTIAL"
        or run.completed_at is None
        or run.failure_code != FAILURE
        or run.failure_count != 0
        or run.requested_count != 553
        or run.success_count != 553
        or metadata.get("runDate") != TARGET.isoformat()
        or metadata.get("executionScope") != NORMAL_CURRENT_DAY
        or metadata.get("scope") != "FULL"
        or metadata.get("executionMode") != "MANUAL"
        or metadata.get("failureCodes") != [FAILURE]
        or metadata.get("providerPointCount") != 552
        or owner.get("authorization") != "EXPLICIT_OWNER_ONCE"
        or owner.get("reentryAllowed") is not False
        or owner.get("previousRunUntouched") is not True
        or not key.endswith(
            f":{NORMAL_CURRENT_DAY}:FULL:OWNER_EXECUTION:{owner.get('executionId')}"
        )
    ):
        reasons.append("HOME_COMPLETION_EXECUTION_CONTRACT_INVALID")
    if metadata.get("ownerHomeCompletion"):
        reasons.append("HOME_COMPLETION_AUTHORIZATION_ALREADY_CLAIMED")
    grouped: dict[str, list[Any]] = defaultdict(list)
    for cp in checkpoints:
        grouped[cp.batch_key].append(cp)
    if COMPLETION_KEY in grouped:
        reasons.append("HOME_COMPLETION_AUTHORIZATION_ALREADY_CLAIMED")
    latest = {}
    for batch_key, events in grouped.items():
        events = sorted(events, key=lambda c: c.attempt_number)
        if [c.attempt_number for c in events] != list(range(1, len(events) + 1)):
            reasons.append("HOME_COMPLETION_CHECKPOINT_CONTINUITY_INVALID")
        for cp in events:
            cp_metadata = cp.metadata_payload or {}
            if (
                run is None
                or cp.run_id != run.id
                or cp_metadata.get("executionScope") != NORMAL_CURRENT_DAY
                or cp_metadata.get("executionKey") != key
                or len(str(cp.checkpoint_hash)) != 64
                or any(c not in "0123456789abcdef" for c in str(cp.checkpoint_hash))
            ):
                reasons.append("HOME_COMPLETION_CHECKPOINT_CONTINUITY_INVALID")
        latest[batch_key] = events[-1]
    for batch_key in (
        "SESSION_VALIDATION",
        "INPUT_READINESS",
        "STATUS_RESOLUTION",
        "FORMAL_MARKET_FACTS:OFFICIAL",
        "A9_B2_FORMAL_PROCESSING",
    ):
        cp = latest.get(batch_key)
        if cp is None or cp.status != "COMPLETED" or cp.failed_count:
            reasons.append("HOME_COMPLETION_PREREQUISITE_INCOMPLETE")
        elif (
            cp.provider_request_count is not None
            or cp.provider_failure_count is not None
            or (cp.metadata_payload or {}).get("providerMetricsApplicability") != "NOT_APPLICABLE"
        ):
            reasons.append("HOME_COMPLETION_NON_PROVIDER_METRICS_INVALID")
    for batch_key, state in (("FINAL_PUBLICATION", "FAILED"), ("COMPLETION", "PARTIAL")):
        if latest.get(batch_key) is None or latest[batch_key].status != state:
            reasons.append("HOME_COMPLETION_TERMINAL_CONTINUITY_INVALID")
    batches = [
        c
        for k, c in latest.items()
        if k.startswith(("FORMAL_MARKET_FACTS:TPE:", "FORMAL_MARKET_FACTS:TWO:"))
    ]
    if (
        not batches
        or any(
            c.status not in {"COMPLETED", "PARTIAL"}
            or c.failed_count
            or c.provider_failure_count != 0
            or c.provider_request_count != c.succeeded_count
            or c.processed_count != c.succeeded_count + c.skipped_count
            or (c.metadata_payload or {}).get("providerMetricsApplicability") != "ACTUAL"
            for c in batches
        )
        or (
            sum(c.processed_count for c in batches) != 553
            or sum(c.succeeded_count for c in batches) != 552
            or sum(c.skipped_count for c in batches) != 1
        )
    ):
        reasons.append("HOME_COMPLETION_INGESTION_NOT_COMPLETE")
    metrics = metadata.get("statusResolutionMetrics") or {}
    if (
        metrics.get("LEGITIMATE_UNAVAILABLE_COUNT") != 1
        or metrics.get("UNRESOLVED_UNAVAILABLE_COUNT") != 0
        or metrics.get("STATUS_AUTHORITY_PROVIDER_FAILURE_COUNT") != 0
        or metrics.get("STATUS_AUTHORITY_MANUAL_OVERRIDE_COUNT") != 0
    ):
        reasons.append("HOME_COMPLETION_STATUS_AUTHORITY_NOT_READY")
    snapshot = metadata.get("topicSnapshot") or {}
    if (snapshot.get("formalTopicDailyState") or {}).get("status") != "SUCCESS" or (
        snapshot.get("formalTopicSnapshotReadback") or {}
    ).get("status") != "PASS":
        reasons.append("HOME_COMPLETION_FORMAL_TOPIC_NOT_READY")
    return {
        "status": "BLOCKED" if reasons else "PASS",
        "reasonCodes": sorted(set(reasons)),
        "runId": str(run.id) if run else None,
        "executionKey": key,
        "executionScope": NORMAL_CURRENT_DAY,
        "normalReentryAllowed": False,
        "newCollectorRunAllowed": False,
        "providerIngestionAllowed": False,
        "comparatorApplyAllowed": False,
        "topicCalculationAllowed": False,
        "separateOwnerAuthorizationRequired": True,
    }


def validate_market_facts(indices: Sequence[Any], aggregates: Sequence[Any]) -> None:
    """Only exact-date official market facts may reach the existing Home writer."""
    if len(indices) != 2 or {f.market for f in indices} != {"TPE", "TWO"}:
        raise PostClosePreconditionError("HOME_COMPLETION_INDEX_NOT_READY")
    for fact in indices:
        if (
            fact.trading_date != TARGET
            or fact.data_status != IndexDataStatus.AVAILABLE
            or fact.source_provider != ("TWSE" if fact.market == "TPE" else "TPEx")
            or not isinstance(fact.value, Decimal)
            or not fact.value.is_finite()
            or fact.value <= 0
            or not isinstance(fact.previous_close, Decimal)
            or not fact.previous_close.is_finite()
            or fact.previous_close <= 0
            or not _valid_response_hash(fact.response_content_hash)
            or not fact.lineage
            or not fact.source_endpoint.startswith(
                "https://www.twse.com.tw/" if fact.market == "TPE" else "https://www.tpex.org.tw/"
            )
        ):
            raise PostClosePreconditionError("HOME_COMPLETION_INDEX_NOT_READY")
    if (
        len(aggregates) != 2
        or {f.market for f in aggregates} != {"TPE", "TWO"}
        or any(
            f.trading_date != TARGET
            or f.data_status != "AVAILABLE"
            or f.source
            != (TWSE_DAILY_AGGREGATE_SOURCE if f.market == "TPE" else TPEX_DAILY_AGGREGATE_SOURCE)
            or not _valid_response_hash(f.response_content_hash)
            or not f.lineage
            for f in aggregates
        )
    ):
        raise PostClosePreconditionError("HOME_COMPLETION_AGGREGATE_NOT_READY")


def _valid_response_hash(value: Any) -> bool:
    return (
        isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)
    )


class OwnerHomeCompletion(PostCloseUpdater):
    """Append-only authorization/checkpoints; never enters collector RUNNING."""

    def __init__(self, session, config, *, run_id: UUID, authorization_id: UUID):
        super().__init__(session, config)
        self.source_run_id = run_id
        self.authorization_id = authorization_id

    def preflight(self) -> dict[str, Any]:
        run = self.session.get(LiveCollectorRun, self.source_run_id)
        checkpoints = list(
            self.session.scalars(
                select(LiveCollectorCheckpoint).where(
                    LiveCollectorCheckpoint.run_id == self.source_run_id
                )
            )
        )
        report = evaluate_home_completion(run, checkpoints)
        if report["status"] != "PASS":
            return report
        owner_id = run.metadata_payload["ownerNormalExecution"]["executionId"]
        try:
            UUID(owner_id)
        except (ValueError, TypeError, AttributeError) as exc:
            raise PostClosePreconditionError("HOME_COMPLETION_OWNER_IDENTITY_INVALID") from exc
        expected_key = (
            f"post-close:{self.config.reference_data_version}:{self.config.calendar_code}:"
            f"{TARGET}:{NORMAL_CURRENT_DAY}:FULL:OWNER_EXECUTION:{owner_id}"
        )
        if report["executionKey"] != expected_key:
            raise PostClosePreconditionError("HOME_COMPLETION_REFERENCE_LINEAGE_MISMATCH")
        context = load_g2_preflight_context(
            self.session,
            target_date=TARGET,
            reference_version=self.config.reference_data_version,
        )
        if not context.context_ready:
            raise PostClosePreconditionError("HOME_COMPLETION_UNIVERSE_NOT_READY")
        self.expected_ids = tuple(
            UUID(m.instrument_ids[c]) for m in context.markets for c in m.instrument_codes
        )
        reconciliation = reconcile_daily_market(
            self.session, TARGET, expected_instrument_ids=self.expected_ids
        )
        if len(self.expected_ids) != 553 or not reconciliation.downstream_ready:
            raise PostClosePreconditionError("HOME_COMPLETION_DAILY_MARKET_NOT_READY")
        rows = read_daily_market_rows(
            self.session, TARGET, expected_instrument_ids=self.expected_ids
        )
        prices = [r for r in rows if r.get("close") is not None]
        if len(prices) != 552 or any(
            r.get("previous_close") is None
            or r["previous_close"] <= 0
            or r.get("previous_close_date") != context.previous_session
            or str(r.get("previous_close_instrument_id")) != str(r["instrument_id"])
            or r.get("previous_close_source") not in {"TWSE_OFFICIAL_DAILY", "TPEX_OFFICIAL_DAILY"}
            or not r.get("previous_close_lineage")
            for r in prices
        ):
            raise PostClosePreconditionError("HOME_COMPLETION_COMPARATOR_NOT_READY")
        readback = self._formal_publication_readback(
            TARGET, run_id=self.source_run_id, execution_scope=NORMAL_CURRENT_DAY
        )
        if (
            readback["topicSnapshot"]["status"] != "PASS"
            or readback["institutionalFlow"]["status"] != "PASS"
        ):
            raise PostClosePreconditionError("HOME_COMPLETION_FORMAL_OUTPUTS_NOT_READY")
        if readback["homePublication"]["status"] == "PASS":
            raise PostClosePreconditionError("HOME_COMPLETION_ALREADY_PUBLISHED")
        if (
            self.session.scalar(
                select(HomePublication.id)
                .where(
                    HomePublication.trading_date == TARGET,
                    HomePublication.publication_state == "PUBLISHED",
                )
                .limit(1)
            )
            is not None
        ):
            raise PostClosePreconditionError("HOME_COMPLETION_DATE_ALREADY_PUBLISHED")
        report.update(
            targetCount=553,
            priceCount=552,
            legitimateUnavailableCount=1,
            formalReadback=readback,
            authorizationId=str(self.authorization_id),
        )
        return report

    def complete_once(self, *, indices: Sequence[Any], aggregates: Sequence[Any]) -> dict[str, Any]:
        validate_market_facts(indices, aggregates)
        self._acquire_session_claim_lock(TARGET)
        run = self.session.scalar(
            select(LiveCollectorRun)
            .where(LiveCollectorRun.id == self.source_run_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        report = self.preflight()
        if report["status"] != "PASS":
            raise PostClosePreconditionError(report["reasonCodes"][0])
        claim = {
            "authorizationId": str(self.authorization_id),
            "operation": "HOME_ONLY_COMPLETION",
            "status": "CLAIMED",
            "previousState": run.status,
            "previousFailureCode": run.failure_code,
            "previousFailureCodes": (run.metadata_payload or {}).get("failureCodes"),
            "previousCompletedAt": run.completed_at.isoformat(),
            "claimedAt": self._now().isoformat(),
            "reentryAllowed": False,
            "normalExecutionRepeated": False,
            "providerIngestionRepeated": False,
        }
        run.metadata_payload = {**run.metadata_payload, "ownerHomeCompletion": claim}
        # Commit the claim first. Concurrent or repeated authorizations cannot
        # reach the writer, including after a process interruption.
        self.session.commit()
        self._active_execution_scope = NORMAL_CURRENT_DAY
        self._active_execution_key = report["executionKey"]
        self._active_run_date = TARGET
        try:
            self._checkpoint_event(
                run_id=run.id, batch_key=COMPLETION_KEY, status="IN_PROGRESS", metadata=claim
            )
            home = materialize_home_v2(
                self.session,
                trading_date=TARGET,
                source_run_id=str(run.id),
                expected_instrument_ids=self.expected_ids,
                market_index_facts=tuple(indices),
                market_aggregate_facts=tuple(aggregates),
            )
            readback = self._formal_publication_readback(
                TARGET, run_id=run.id, execution_scope=NORMAL_CURRENT_DAY
            )
            if home.get("publicationState") != "PUBLISHED" or readback["status"] != "PASS":
                raise PostClosePreconditionError("HOME_COMPLETION_PUBLICATION_READBACK_NOT_READY")
            self._ensure_completed_checkpoint(
                run_id=run.id,
                batch_key="FINAL_PUBLICATION",
                metadata={"formalPublication": readback, "homeOnlyCompletion": claim},
            )
            self._checkpoint_event(
                run_id=run.id,
                batch_key="COMPLETION",
                status="COMPLETED",
                metadata={"homeOnlyCompletion": claim, "readback": readback},
            )
            self._checkpoint_event(
                run_id=run.id,
                batch_key=COMPLETION_KEY,
                status="COMPLETED",
                metadata={**claim, "status": "COMPLETED", "readback": readback},
            )
            metadata = dict(run.metadata_payload)
            snapshot = dict(metadata["topicSnapshot"])
            snapshot.update(homePublication=home, formalPublicationReadback=readback)
            metadata.update(
                topicSnapshot=snapshot,
                failureCodes=[],
                ownerHomeCompletion={
                    **claim,
                    "status": "COMPLETED",
                    "publicationId": home["publicationId"],
                    "completedAt": self._now().isoformat(),
                },
            )
            metadata["forwardAutomation"] = {
                **metadata.get("forwardAutomation", {}),
                "status": "SUCCESS",
            }
            run.metadata_payload = _json_safe(metadata)
            run.status, run.failure_code, run.failure_message = "SUCCESS", None, None
            run.freshness_state = "FRESH"
            run.completed_at = run.heartbeat_at = run.updated_at = self._now()
            self.session.commit()
            return {
                "status": "PASS",
                "runId": str(run.id),
                "normalRunStatus": "SUCCESS",
                "homePublication": home,
                "formalReadback": readback,
                "providerIngestionRepeated": False,
                "newCollectorRunCreated": False,
            }
        except Exception as exc:
            self.session.rollback()
            run = self.session.get(LiveCollectorRun, self.source_run_id)
            failure = {
                **claim,
                "status": "FAILED",
                "exceptionClass": type(exc).__name__,
                "failureCode": getattr(exc, "code", "HOME_COMPLETION_ORCHESTRATION_FAILURE"),
                "operatorActionRequired": "REVIEW_NEW_AUTHORIZATION_CONTRACT",
            }
            run.metadata_payload = _json_safe(
                {**run.metadata_payload, "ownerHomeCompletion": failure}
            )
            # The collector stays terminal PARTIAL. Even a stopped process
            # cannot leave a zombie RUNNING collector or permit another claim.
            self.session.commit()
            self._checkpoint_event(
                run_id=run.id,
                batch_key=COMPLETION_KEY,
                status="FAILED",
                failed_count=1,
                metadata=failure,
            )
            raise
