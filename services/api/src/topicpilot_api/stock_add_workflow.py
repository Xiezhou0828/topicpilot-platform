"""Fail-closed planning primitives for the governed stock-add workflow.

This module intentionally does not connect to a database or perform writes.
It classifies live authority reads, produces an immutable approval digest, and
tracks resumable checkpoints for the separately authorized operator path.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

MASTER_MATCH_FOUND = "MATCH_FOUND"
MASTER_NO_MATCH = "NO_MATCH_CONFIRMED"
MASTER_RETRIEVAL_BLOCKED = "RETRIEVAL_BLOCKED"

TOPIC_OFFICIAL_CORE = "OFFICIAL_CORE"
TOPIC_OFFICIAL_ADJACENT = "OFFICIAL_ADJACENT"
TOPIC_INFERENCE = "INFERENCE_ONLY"
TOPIC_CONFLICT = "SOURCE_CONFLICT"
TOPIC_INSUFFICIENT = "INSUFFICIENT_EVIDENCE"

CHECKPOINTS = (
    "MASTER_DATA_VERIFIED",
    "TOPIC_RELATIONS_VERIFIED",
    "REFERENCE_VERSION_ACTIVATED",
    "G1_G2_VERIFIED",
    "POST_CLOSE_VERIFIED",
)


@dataclass(frozen=True)
class TopicAssessment:
    topic_id: str | None
    slug: str | None
    name: str
    evidence_basis: str
    evidence_summary: str
    source_urls: tuple[str, ...] = ()
    active: bool = True


@dataclass(frozen=True)
class AuthorityReadEvidence:
    source: str
    environment: str
    read_at: str
    complete: bool
    sha256: str
    record_count: int | None = None
    page_count: int | None = None
    scope: str | None = None
    as_of: str | None = None

    @property
    def verified_current_read(self) -> bool:
        if not all(
            isinstance(value, str)
            for value in (self.source, self.environment, self.read_at, self.sha256)
        ):
            return False
        source = self.source.strip().casefold()
        try:
            read_at = datetime.fromisoformat(self.read_at.replace("Z", "+00:00"))
        except ValueError:
            return False
        now = datetime.now(UTC)
        age = now - read_at if read_at.tzinfo is not None else timedelta.max
        return (
            (
                source.endswith("formal read api")
                or source == "topicpilot protected production catalog readback"
            )
            and self.environment == "PRODUCTION_READ_ONLY"
            and timedelta(0) <= age <= timedelta(minutes=15)
            and self.complete is True
            and len(self.sha256) == 64
            and all(char in "0123456789abcdef" for char in self.sha256.lower())
        )


@dataclass(frozen=True)
class TopicDecision:
    topic_id: str | None
    slug: str | None
    name: str
    decision: str
    relation_type: str | None
    weight: float | None
    reason: str
    evidence_summary: str
    source_urls: tuple[str, ...]


@dataclass(frozen=True)
class StockAddPlan:
    stock_code: str
    market: str
    plan_status: str
    research_status: str
    master_status: str
    topic_catalog_status: str
    topic_decisions: tuple[TopicDecision, ...]
    research_package_sha256: str
    master_read_evidence: AuthorityReadEvidence | None
    topic_catalog_read_evidence: AuthorityReadEvidence | None
    reference_bundle_sha256: str | None
    plan_sha256: str

    @property
    def final_confirmation(self) -> str | None:
        if (
            self.plan_status != "FINAL_APPROVAL_PENDING"
            or not _is_sha256(self.plan_sha256)
            or self.master_read_evidence is None
            or not self.master_read_evidence.verified_current_read
            or self.topic_catalog_read_evidence is None
            or not self.topic_catalog_read_evidence.verified_current_read
        ):
            return None
        return f"APPLY STOCK ADD {self.stock_code} {self.plan_sha256}"


@dataclass(frozen=True)
class OperationEvent:
    stage: str
    status: str
    artifact_sha256: str


@dataclass(frozen=True)
class StockAddOperation:
    operation_id: str
    stock_code: str
    plan_sha256: str
    events: tuple[OperationEvent, ...] = field(default_factory=tuple)


class StockAddWorkflowError(ValueError):
    """Raised when an add plan or operation tries to cross a failed gate."""


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _publication_ready(package: dict[str, Any]) -> bool:
    projection = package.get("frontendProjection")
    if not isinstance(projection, dict):
        return False
    governance = projection.get("researchGovernance")
    publication = governance.get("publication") if isinstance(governance, dict) else None
    if not isinstance(publication, dict):
        return False
    evidence = publication.get("approvalEvidence")
    return (
        publication.get("publicationStatus") == "PUBLISHED"
        and publication.get("ownerReviewStatus") == "APPROVED"
        and publication.get("sourceRightsStatus") == "APPROVED"
        and isinstance(evidence, dict)
        and all(evidence.get(key) for key in ("decisionId", "reviewer", "approvedAt"))
    )


def classify_topic(assessment: TopicAssessment) -> TopicDecision:
    """Map only direct official evidence to a fixed relation and weight."""
    base = {
        "topic_id": assessment.topic_id,
        "slug": assessment.slug,
        "name": assessment.name,
        "evidence_summary": assessment.evidence_summary,
        "source_urls": assessment.source_urls,
    }
    if not assessment.active or not assessment.topic_id or not assessment.slug:
        return TopicDecision(
            **base,
            decision="SUGGESTION_ONLY",
            relation_type=None,
            weight=None,
            reason="TOPIC_NOT_CONFIRMED_ACTIVE_IN_FORMAL_CATALOG",
        )
    if assessment.evidence_basis == TOPIC_OFFICIAL_CORE and assessment.source_urls:
        return TopicDecision(
            **base,
            decision="RELATION_CANDIDATE",
            relation_type="PRIMARY",
            weight=1.0,
            reason="OFFICIAL_DIRECT_EVIDENCE_FOR_CORE_BUSINESS",
        )
    if assessment.evidence_basis == TOPIC_OFFICIAL_ADJACENT and assessment.source_urls:
        return TopicDecision(
            **base,
            decision="RELATION_CANDIDATE",
            relation_type="SECONDARY",
            weight=0.5,
            reason="OFFICIAL_DIRECT_EVIDENCE_FOR_ADJACENT_BUSINESS",
        )
    reasons = {
        TOPIC_INFERENCE: "INFERENCE_IS_NOT_FORMAL_RELATION_EVIDENCE",
        TOPIC_CONFLICT: "SOURCE_CONFLICT_REQUIRES_REVIEW",
        TOPIC_INSUFFICIENT: "INSUFFICIENT_DIRECT_EVIDENCE",
    }
    return TopicDecision(
        **base,
        decision="SUGGESTION_ONLY",
        relation_type=None,
        weight=None,
        reason=reasons.get(assessment.evidence_basis, "UNSUPPORTED_EVIDENCE_BASIS"),
    )


def _deduplicate_assessments(
    assessments: tuple[TopicAssessment, ...],
) -> tuple[TopicAssessment, ...]:
    by_identity: dict[str, list[TopicAssessment]] = {}
    for assessment in assessments:
        identity = assessment.topic_id or assessment.slug or assessment.name.strip().casefold()
        by_identity.setdefault(identity, []).append(assessment)
    result: list[TopicAssessment] = []
    for matches in by_identity.values():
        first = matches[0]
        bases = {item.evidence_basis for item in matches}
        summaries = tuple(
            dict.fromkeys(item.evidence_summary for item in matches if item.evidence_summary)
        )
        urls = tuple(dict.fromkeys(url for item in matches for url in item.source_urls))
        result.append(
            TopicAssessment(
                topic_id=first.topic_id,
                slug=first.slug,
                name=first.name,
                evidence_basis=(TOPIC_CONFLICT if len(bases) > 1 else first.evidence_basis),
                evidence_summary="、".join(summaries),
                source_urls=urls,
                active=all(item.active for item in matches),
            )
        )
    return tuple(result)


def build_stock_add_plan(
    *,
    stock_code: str,
    market: str,
    package: dict[str, Any],
    master_status: str,
    master_read_evidence: AuthorityReadEvidence | None,
    topic_catalog_status: str,
    topic_catalog_read_evidence: AuthorityReadEvidence | None,
    assessments: tuple[TopicAssessment, ...] = (),
    reference_bundle_sha256: str | None = None,
) -> StockAddPlan:
    """Build a digest-bound review plan; never writes or treats stale reads as authority."""
    code = stock_code.strip()
    market_code = market.strip().upper()
    company = package.get("company") if isinstance(package, dict) else None
    package_code = str(company.get("stockCode", "")).strip() if isinstance(company, dict) else ""
    if not code or package_code != code:
        raise StockAddWorkflowError("RESEARCH_PACKAGE_IDENTITY_MISMATCH")
    if market_code not in {"TPE", "TWO"}:
        raise StockAddWorkflowError("UNSUPPORTED_MARKET_CODE")
    if master_status not in {MASTER_MATCH_FOUND, MASTER_NO_MATCH, MASTER_RETRIEVAL_BLOCKED}:
        raise StockAddWorkflowError("INVALID_MASTER_CHECK_STATUS")

    research_ready = _publication_ready(package)
    research_status = "RESEARCH_READY" if research_ready else "RESEARCH_REVIEW_REQUIRED"
    master_evidence_valid = bool(
        master_read_evidence and master_read_evidence.verified_current_read
    )
    topic_status_valid = bool(
        topic_catalog_status == "READY"
        and topic_catalog_read_evidence
        and topic_catalog_read_evidence.verified_current_read
    )
    # Research-to-catalog comparison is independent of both the stock-master
    # result and the publication gate. It may produce review candidates while
    # the package is still a draft or the master read is blocked; neither case
    # makes the candidates writable or advances the add plan past its gates.
    decisions = (
        tuple(classify_topic(item) for item in _deduplicate_assessments(assessments))
        if topic_status_valid and master_status != MASTER_MATCH_FOUND
        else ()
    )

    if master_status == MASTER_RETRIEVAL_BLOCKED or not master_evidence_valid:
        plan_status = "MASTER_CHECK_BLOCKED"
    elif master_status == MASTER_MATCH_FOUND:
        plan_status = "MASTER_MATCH_FOUND"
    elif not research_ready:
        plan_status = "RESEARCH_REVIEW_REQUIRED"
    elif not topic_status_valid:
        plan_status = "TOPIC_CATALOG_BLOCKED"
    elif not reference_bundle_sha256:
        plan_status = "REFERENCE_UNIVERSE_PENDING"
    else:
        plan_status = "FINAL_APPROVAL_PENDING"

    research_hash = canonical_sha256(package)
    plan_content = {
        "stockCode": code,
        "market": market_code,
        "planStatus": plan_status,
        "researchStatus": research_status,
        "masterStatus": master_status,
        "topicCatalogStatus": topic_catalog_status,
        "topicDecisions": [asdict(item) for item in decisions],
        "researchPackageSha256": research_hash,
        "masterReadEvidence": asdict(master_read_evidence) if master_read_evidence else None,
        "topicCatalogReadEvidence": (
            asdict(topic_catalog_read_evidence) if topic_catalog_read_evidence else None
        ),
        "referenceBundleSha256": reference_bundle_sha256,
    }
    return StockAddPlan(
        stock_code=code,
        market=market_code,
        plan_status=plan_status,
        research_status=research_status,
        master_status=master_status,
        topic_catalog_status=topic_catalog_status,
        topic_decisions=decisions,
        research_package_sha256=research_hash,
        master_read_evidence=master_read_evidence,
        topic_catalog_read_evidence=topic_catalog_read_evidence,
        reference_bundle_sha256=reference_bundle_sha256,
        plan_sha256=canonical_sha256(plan_content),
    )


def verify_final_confirmation(plan: StockAddPlan, confirmation: str) -> None:
    expected = plan.final_confirmation
    if expected is None:
        raise StockAddWorkflowError("PLAN_NOT_READY_FOR_FINAL_APPROVAL")
    if confirmation.strip() != expected:
        raise StockAddWorkflowError("FINAL_CONFIRMATION_HASH_MISMATCH")


def new_operation(plan: StockAddPlan) -> StockAddOperation:
    if plan.final_confirmation is None:
        raise StockAddWorkflowError("PLAN_NOT_READY_FOR_OPERATION")
    return StockAddOperation(
        operation_id=f"stock-add:{plan.stock_code}:{plan.plan_sha256}",
        stock_code=plan.stock_code,
        plan_sha256=plan.plan_sha256,
    )


def operation_to_record(operation: StockAddOperation) -> dict[str, Any]:
    """Return a versioned checkpoint record suitable for durable external storage."""
    return {
        "schemaVersion": "stock-add-operation.v2",
        "operationId": operation.operation_id,
        "stockCode": operation.stock_code,
        "planSha256": operation.plan_sha256,
        "events": [asdict(event) for event in operation.events],
    }


def operation_from_record(record: dict[str, Any]) -> StockAddOperation:
    """Validate/replay a persisted record so interrupted work can resume safely."""
    if not isinstance(record, dict):
        raise StockAddWorkflowError("INVALID_OPERATION_RECORD_FIELDS")
    if set(record) != {
        "schemaVersion",
        "operationId",
        "stockCode",
        "planSha256",
        "events",
    }:
        raise StockAddWorkflowError("INVALID_OPERATION_RECORD_FIELDS")
    if record.get("schemaVersion") != "stock-add-operation.v2":
        raise StockAddWorkflowError("UNSUPPORTED_OPERATION_RECORD_VERSION")
    plan_sha256 = record.get("planSha256")
    operation_id = record.get("operationId")
    stock_code = record.get("stockCode")
    if (
        not _is_sha256(plan_sha256)
        or not isinstance(operation_id, str)
        or not isinstance(stock_code, str)
        or not stock_code.isdigit()
    ):
        raise StockAddWorkflowError("INVALID_OPERATION_RECORD_IDENTITY")
    if operation_id != f"stock-add:{stock_code}:{plan_sha256}":
        raise StockAddWorkflowError("INVALID_OPERATION_RECORD_IDENTITY")
    operation = StockAddOperation(
        operation_id=operation_id,
        stock_code=stock_code,
        plan_sha256=plan_sha256,
    )
    events = record.get("events")
    if not isinstance(events, list):
        raise StockAddWorkflowError("INVALID_OPERATION_RECORD_EVENTS")
    for event in events:
        if not isinstance(event, dict) or set(event) != {
            "stage",
            "status",
            "artifact_sha256",
        }:
            raise StockAddWorkflowError("INVALID_OPERATION_RECORD_EVENT")
        operation = record_checkpoint(
            operation,
            plan_sha256=plan_sha256,
            stage=str(event.get("stage", "")),
            status=str(event.get("status", "")),
            artifact_sha256=str(event.get("artifact_sha256", "")),
        )
    return operation


def record_checkpoint(
    operation: StockAddOperation,
    *,
    plan_sha256: str,
    stage: str,
    status: str,
    artifact_sha256: str,
) -> StockAddOperation:
    """Append an idempotent checkpoint and prevent skipping failed stages."""
    if (
        plan_sha256 != operation.plan_sha256
        or not _is_sha256(operation.plan_sha256)
        or not isinstance(operation.stock_code, str)
        or not operation.stock_code.isdigit()
        or operation.operation_id != f"stock-add:{operation.stock_code}:{operation.plan_sha256}"
    ):
        raise StockAddWorkflowError("OPERATION_PLAN_HASH_MISMATCH")
    if (
        stage not in CHECKPOINTS
        or status not in {"PASS", "BLOCKED"}
        or not _is_sha256(artifact_sha256)
    ):
        raise StockAddWorkflowError("INVALID_CHECKPOINT")
    exact = OperationEvent(stage, status, artifact_sha256)
    if exact in operation.events:
        return operation

    passed = {event.stage for event in operation.events if event.status == "PASS"}
    next_index = len(passed)
    if next_index >= len(CHECKPOINTS) or CHECKPOINTS[next_index] != stage:
        raise StockAddWorkflowError("CHECKPOINT_OUT_OF_ORDER")
    operation = StockAddOperation(
        operation_id=operation.operation_id,
        stock_code=operation.stock_code,
        plan_sha256=operation.plan_sha256,
        events=(*operation.events, exact),
    )
    return operation


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value.lower())
    )
