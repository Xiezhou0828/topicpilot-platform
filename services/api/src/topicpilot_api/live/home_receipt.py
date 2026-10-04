"""Owner-governed receipt closure for an already committed Home. Never a writer retry."""

from __future__ import annotations

from collections import defaultdict
from types import SimpleNamespace
from uuid import UUID

from sqlalchemy import select

from topicpilot_api.orm import HomePublication, LiveCollectorCheckpoint, LiveCollectorRun

from .home_completion import COMPLETION_KEY, FAILURE, TARGET, evaluate_home_completion
from .post_close import NORMAL_CURRENT_DAY, PostClosePreconditionError, PostCloseUpdater, _json_safe

RECEIPT_KEY = "OWNER_PUBLISHED_HOME_RECEIPT"


class OwnerPublishedHomeReceipt(PostCloseUpdater):
    """Read committed outputs, then atomically close only run metadata and one receipt event.

    The failed Home authorization and all existing events remain immutable. This
    class has no provider, comparator, Topic, Home materializer, or run_once call.
    """

    def __init__(self, session, config, *, run_id, publication_id, completion_id, authorization_id):
        super().__init__(session, config)
        self.source_run_id = run_id
        self.publication_id = publication_id
        self.completion_id = completion_id
        self.authorization_id = authorization_id

    def preflight(self):
        def require(condition, code):
            if not condition:
                raise PostClosePreconditionError(code)

        run = self.session.get(LiveCollectorRun, self.source_run_id)
        require(run is not None, "HOME_RECEIPT_RUN_NOT_FOUND")
        metadata = run.metadata_payload or {}
        failed = metadata.get("ownerHomeCompletion") or {}
        require(
            failed.get("authorizationId") == str(self.completion_id)
            and failed.get("operation") == "HOME_ONLY_COMPLETION"
            and failed.get("status") == "FAILED"
            and failed.get("exceptionClass") == "TypeError"
            and failed.get("failureCode") == "HOME_COMPLETION_ORCHESTRATION_FAILURE"
            and failed.get("previousState") == "PARTIAL"
            and failed.get("previousFailureCode") == FAILURE
            and failed.get("previousFailureCodes") == [FAILURE]
            and failed.get("reentryAllowed") is False
            and failed.get("normalExecutionRepeated") is False
            and failed.get("providerIngestionRepeated") is False,
            "HOME_RECEIPT_FAILED_CLAIM_INVALID",
        )
        receipt = metadata.get("ownerPublishedHomeReceipt")
        require(
            (not receipt and run.status == "PARTIAL" and run.failure_code == FAILURE)
            or (
                receipt
                and run.status == "SUCCESS"
                and run.failure_code is None
                and metadata.get("failureCodes") == []
                and receipt.get("status") == "COMPLETED"
                and receipt.get("authorizationId") == str(self.authorization_id)
                and receipt.get("publicationId") == str(self.publication_id)
                and receipt.get("completionAuthorizationId") == str(self.completion_id)
            ),
            "HOME_RECEIPT_STATE_OR_AUTHORIZATION_INVALID",
        )
        checkpoints = list(
            self.session.scalars(
                select(LiveCollectorCheckpoint).where(LiveCollectorCheckpoint.run_id == run.id)
            )
        )
        grouped = defaultdict(list)
        key = metadata.get("executionKey")
        for cp in checkpoints:
            cp_metadata = cp.metadata_payload or {}
            require(
                cp_metadata.get("executionKey") == key
                and cp_metadata.get("executionScope") == NORMAL_CURRENT_DAY,
                "HOME_RECEIPT_CONTINUITY_INVALID",
            )
            grouped[cp.batch_key].append(cp)
        for events in grouped.values():
            events.sort(key=lambda cp: cp.attempt_number)
            require(
                [cp.attempt_number for cp in events] == list(range(1, len(events) + 1)),
                "HOME_RECEIPT_CONTINUITY_INVALID",
            )
        home_events = grouped.get(COMPLETION_KEY, [])
        require(
            [cp.status for cp in home_events] == ["IN_PROGRESS", "COMPLETED", "FAILED"]
            and all(
                (cp.metadata_payload or {}).get("authorizationId") == str(self.completion_id)
                for cp in home_events
            )
            and home_events[-1].metadata_payload.get("exceptionClass") == "TypeError"
            and home_events[-1].metadata_payload.get("failureCode") == failed["failureCode"],
            "HOME_RECEIPT_HOME_EVENT_INVALID",
        )
        for batch in ("FINAL_PUBLICATION", "COMPLETION"):
            events = grouped.get(batch, [])
            require(
                len(events) == 2 and events[-1].status == "COMPLETED",
                "HOME_RECEIPT_PUBLICATION_EVENT_INVALID",
            )
            event_readback = events[-1].metadata_payload.get(
                "formalPublication" if batch == "FINAL_PUBLICATION" else "readback", {}
            )
            require(
                event_readback.get("status") == "PASS"
                and event_readback.get("homePublication", {}).get("publicationId")
                == str(self.publication_id),
                "HOME_RECEIPT_PUBLICATION_EVENT_INVALID",
            )
        require(bool(receipt) == bool(grouped.get(RECEIPT_KEY)), "HOME_RECEIPT_CONTINUITY_INVALID")
        if receipt:
            events = grouped[RECEIPT_KEY]
            require(
                len(events) == 1
                and events[0].status == "COMPLETED"
                and events[0].metadata_payload.get("authorizationId") == str(self.authorization_id),
                "HOME_RECEIPT_CONTINUITY_INVALID",
            )
        # Review the original collection gates without changing or reinterpreting
        # any stored event. Only the original failed publication events are used.
        review_metadata = {**metadata, "failureCodes": [FAILURE]}
        review_metadata.pop("ownerHomeCompletion", None)
        review = SimpleNamespace(
            **{
                name: getattr(run, name)
                for name in (
                    "id",
                    "run_type",
                    "completed_at",
                    "failure_count",
                    "requested_count",
                    "success_count",
                )
            },
            status="PARTIAL",
            failure_code=FAILURE,
            metadata_payload=review_metadata,
        )
        original_events = [
            cp
            for cp in checkpoints
            if cp.batch_key not in (COMPLETION_KEY, RECEIPT_KEY)
            and (cp.batch_key not in ("FINAL_PUBLICATION", "COMPLETION") or cp.attempt_number == 1)
        ]
        report = evaluate_home_completion(review, original_events)
        require(report["status"] == "PASS", "HOME_RECEIPT_ORIGINAL_GATES_INVALID")
        owner_id = metadata["ownerNormalExecution"]["executionId"]
        try:
            UUID(owner_id)
        except (ValueError, TypeError, AttributeError) as exc:
            raise PostClosePreconditionError("HOME_RECEIPT_IDENTITY_INVALID") from exc
        require(
            key == f"post-close:{self.config.reference_data_version}:{self.config.calendar_code}:"
            f"{TARGET}:{NORMAL_CURRENT_DAY}:FULL:OWNER_EXECUTION:{owner_id}",
            "HOME_RECEIPT_REFERENCE_LINEAGE_INVALID",
        )
        publications = list(
            self.session.scalars(
                select(HomePublication).where(
                    HomePublication.trading_date == TARGET,
                    HomePublication.publication_state == "PUBLISHED",
                )
            )
        )
        require(len(publications) == 1, "HOME_RECEIPT_PUBLICATION_NOT_UNIQUE")
        home = publications[0]
        require(
            home.id == self.publication_id
            and home.source_run_id == str(run.id)
            and home.published_at is not None
            and bool(home.lineage_hash),
            "HOME_RECEIPT_PUBLICATION_LINEAGE_INVALID",
        )
        readback = self._formal_publication_readback(
            TARGET, run_id=run.id, execution_scope=NORMAL_CURRENT_DAY
        )
        require(
            readback.get("status") == "PASS"
            and readback.get("homePublication", {}).get("publicationId") == str(home.id),
            "HOME_RECEIPT_FORMAL_READBACK_FAILED",
        )
        return {
            "status": "PASS",
            "runId": str(run.id),
            "executionKey": key,
            "authorizationId": str(self.authorization_id),
            "formalReadback": readback,
            "homePublication": {
                "publicationId": str(home.id),
                "tradingDate": TARGET,
                "publicationState": "PUBLISHED",
                "publishedAt": home.published_at,
                "sourceDatasetId": home.source_dataset_id,
            },
            "alreadyFinalized": bool(receipt),
            "homeWriterAllowed": False,
            "providerIngestionAllowed": False,
            "normalReentryAllowed": False,
        }

    def complete_once(self):
        self._acquire_session_claim_lock(TARGET)
        run = self.session.scalar(
            select(LiveCollectorRun)
            .where(LiveCollectorRun.id == self.source_run_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        report = self.preflight()
        if report["alreadyFinalized"]:
            return _json_safe({**report, "productionMutated": False})
        receipt = {
            "authorizationId": str(self.authorization_id),
            "status": "COMPLETED",
            "operation": "PUBLISHED_HOME_RECEIPT_ONLY",
            "completionAuthorizationId": str(self.completion_id),
            "publicationId": str(self.publication_id),
            "previousState": run.status,
            "previousFailureCode": run.failure_code,
            "previousFailureCodes": run.metadata_payload.get("failureCodes"),
            "previousCompletedAt": run.completed_at,
            "completedAt": self._now(),
            "homeWriterRepeated": False,
            "providerIngestionRepeated": False,
            "normalExecutionRepeated": False,
            "reentryAllowed": False,
        }
        metadata = dict(run.metadata_payload)
        snapshot = dict(metadata["topicSnapshot"])
        snapshot.update(
            homePublication=report["homePublication"],
            formalPublicationReadback=report["formalReadback"],
        )
        metadata.update(topicSnapshot=snapshot, failureCodes=[], ownerPublishedHomeReceipt=receipt)
        metadata["forwardAutomation"] = {
            **metadata.get("forwardAutomation", {}),
            "status": "SUCCESS",
        }
        run.metadata_payload = _json_safe(metadata)
        run.status, run.failure_code, run.failure_message = "SUCCESS", None, None
        run.freshness_state = "FRESH"
        run.completed_at = run.heartbeat_at = run.updated_at = self._now()
        self._active_execution_scope = NORMAL_CURRENT_DAY
        self._active_execution_key = report["executionKey"]
        # The event helper commits this metadata update and exactly one event in
        # the SAME transaction. Failure rolls both back; no partial claim/run.
        try:
            self._checkpoint_event(
                run_id=run.id,
                batch_key=RECEIPT_KEY,
                status="COMPLETED",
                metadata={**receipt, "readback": report["formalReadback"]},
            )
        except Exception:
            self.session.rollback()
            raise
        return _json_safe({**report, "normalRunStatus": "SUCCESS", "productionMutated": True})
