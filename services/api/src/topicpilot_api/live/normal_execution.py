"""One Owner-authorized fresh NORMAL_CURRENT_DAY identity after a terminal failure.

No failed run is resumed or updated. Existing ingestion's point idempotency
remains unchanged. A claimed identity can never be re-entered through this
operator surface, even after failure; a new authorization requires review.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import select

from topicpilot_api.orm import LiveCollectorCheckpoint

from .post_close import NORMAL_CURRENT_DAY, PostClosePreconditionError, PostCloseUpdater


def evaluate_normal_identity(
    runs: list[Any],
    checkpoints: list[Any],
    *,
    run_date: date,
    supersedes_run_id: UUID,
    reference_version: str,
    calendar_code: str,
) -> dict[str, Any]:
    reasons = []
    old = next((r for r in runs if r.id == supersedes_run_id), None)
    old_key = f"post-close:{reference_version}:{calendar_code}:{run_date}:FULL"
    scoped_key = (
        f"post-close:{reference_version}:{calendar_code}:{run_date}:{NORMAL_CURRENT_DAY}:FULL"
    )
    if any(r.status == "RUNNING" for r in runs):
        reasons.append("NORMAL_DATE_HAS_RUNNING_RUN")
    if any(r.status == "SUCCESS" for r in runs):
        reasons.append("NORMAL_DATE_ALREADY_SUCCESSFUL")
    if any(
        ":OWNER_EXECUTION:" in str((r.metadata_payload or {}).get("executionKey", "")) for r in runs
    ):
        reasons.append("OWNER_NORMAL_AUTHORIZATION_ALREADY_CLAIMED")
    metadata = (old.metadata_payload or {}) if old else {}
    if (
        old is None
        or old.status not in {"FAILED", "PARTIAL"}
        or old.completed_at is None
        or old.heartbeat_at is None
        or metadata.get("runDate") != run_date.isoformat()
        or metadata.get("executionKey") not in {old_key, scoped_key}
        or metadata.get("scope", "FULL") != "FULL"
        or metadata.get("executionScope") not in {None, NORMAL_CURRENT_DAY}
        or metadata.get("executionMode") == "RECOVERY"
        or metadata.get("recoveryOfRunId")
    ):
        reasons.append("PREVIOUS_NORMAL_RUN_CONTRACT_INVALID")
    grouped = defaultdict(list)
    for cp in checkpoints:
        grouped[cp.batch_key].append(cp)
    continuity = bool(grouped)
    for attempts in grouped.values():
        attempts.sort(key=lambda cp: cp.attempt_number)
        continuity = continuity and [c.attempt_number for c in attempts] == list(
            range(1, len(attempts) + 1)
        )
        for cp in attempts:
            scope = (cp.metadata_payload or {}).get("executionScope")
            key = (cp.metadata_payload or {}).get("executionKey")
            continuity = (
                continuity
                and cp.run_id == supersedes_run_id
                and len(str(cp.checkpoint_hash)) == 64
                and all(c in "0123456789abcdef" for c in str(cp.checkpoint_hash))
                and scope in {None, NORMAL_CURRENT_DAY}
                and key in {None, old_key, scoped_key}
            )
        continuity = continuity and attempts[-1].status in {"COMPLETED", "PARTIAL", "FAILED"}
    completion = grouped.get("COMPLETION", [])
    continuity = continuity and bool(completion) and completion[-1].status in {"PARTIAL", "FAILED"}
    if not continuity:
        reasons.append("PREVIOUS_CHECKPOINT_CONTINUITY_INVALID")
    return {
        "status": "PASS" if not reasons else "BLOCKED",
        "reasonCodes": reasons,
        "previousRunId": str(supersedes_run_id),
        "previousStatus": old.status if old else None,
        "previousExecutionKey": metadata.get("executionKey"),
        "previousScope": metadata.get("executionScope", "LEGACY_NORMAL_CURRENT_DAY"),
        "previousHeartbeat": old.heartbeat_at.isoformat() if old and old.heartbeat_at else None,
        "previousCompletedAt": old.completed_at.isoformat() if old and old.completed_at else None,
        "resumeCount": metadata.get("resumeCount", 0),
        "checkpointCount": len(checkpoints),
        "checkpointContinuity": continuity,
        "completedCheckpointReuse": "NONE",
        "providerPointReuse": "EXISTING_RAW_TIMELINE_CANONICAL_IDEMPOTENCY",
        "oldRunMutationAllowed": False,
        "newRecoveryRunAllowed": False,
        "executionScope": NORMAL_CURRENT_DAY,
        "operatorAuthorizationRequired": True,
    }


class OwnerNormalExecution(PostCloseUpdater):
    def __init__(self, session, config, *, execution_id: UUID, supersedes_run_id: UUID, **kwargs):
        super().__init__(session, config, **kwargs)
        self.execution_id = execution_id
        self.supersedes_run_id = supersedes_run_id

    def identity_preflight(self, run_date: date) -> dict[str, Any]:
        checkpoints = list(
            self.session.scalars(
                select(LiveCollectorCheckpoint).where(
                    LiveCollectorCheckpoint.run_id == self.supersedes_run_id
                )
            )
        )
        report = evaluate_normal_identity(
            self._runs_for_date(run_date),
            checkpoints,
            run_date=run_date,
            supersedes_run_id=self.supersedes_run_id,
            reference_version=self.config.reference_data_version,
            calendar_code=self.config.calendar_code,
        )
        report["newExecutionKey"] = self._execution_key(run_date)
        return report

    def _execution_key(self, run_date, *, target_symbols=None, execution_mode="MANUAL"):
        if execution_mode != "MANUAL" or target_symbols is not None:
            raise PostClosePreconditionError("OWNER_EXECUTION_REQUIRES_FULL_NORMAL_MANUAL")
        return (
            super()._execution_key(run_date, execution_mode="MANUAL")
            + f":OWNER_EXECUTION:{self.execution_id}"
        )

    def _idempotent_result(self, run_date):
        # The explicit owner identity must be validated under the session lock;
        # never silently reuse a different successful or failed execution.
        return None

    def _find_existing_run(self, run_date, *, target_symbols=None, execution_mode="MANUAL"):
        key = self._execution_key(
            run_date, target_symbols=target_symbols, execution_mode=execution_mode
        )
        return next(
            (
                r
                for r in self._runs_for_date(run_date)
                if (r.metadata_payload or {}).get("executionKey") == key
            ),
            None,
        )

    def _prepare_run(self, **kwargs):
        if kwargs["allow_terminal_recovery"] or kwargs["is_targeted"]:
            raise PostClosePreconditionError("OWNER_EXECUTION_IS_NOT_RECOVERY")
        self._acquire_session_claim_lock(kwargs["run_date"])
        report = self.identity_preflight(kwargs["run_date"])
        if report["status"] != "PASS":
            raise PostClosePreconditionError(report["reasonCodes"][0])
        return super()._prepare_run(**kwargs)

    def _create_run(self, *args, **kwargs):
        run = super()._create_run(*args, **kwargs)
        self._set_active_run(run.id)
        metadata = dict(run.metadata_payload or {})
        metadata["ownerNormalExecution"] = {
            "executionId": str(self.execution_id),
            "previousRunId": str(self.supersedes_run_id),
            "authorization": "EXPLICIT_OWNER_ONCE",
            "previousRunUntouched": True,
            "reentryAllowed": False,
            "completedCheckpointReuse": "NONE",
            "providerPointReuse": "EXISTING_RAW_TIMELINE_CANONICAL_IDEMPOTENCY",
        }
        run.metadata_payload = metadata
        self.session.commit()
        return run
