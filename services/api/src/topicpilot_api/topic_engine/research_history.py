"""Point-in-time evidence bridge for research-only Topic Formula replay."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from statistics import fmean
from typing import Any

from .aggregation import AggregateStatus, AggregationResult, FeatureAggregate, QualitySummary
from .features.contracts import FeatureResult, FeatureStatus
from .research import RESEARCH_ONLY, FormulaResearchValidationError
from .research_corpus import (
    FormulaResearchCorpus,
    ResearchCorpusCase,
    create_formula_research_corpus,
)

HISTORICAL_EVIDENCE_SCHEMA_VERSION = "topic-formula-historical-evidence.v1"
POSITIVE = "POSITIVE"
UNCHANGED = "UNCHANGED"
NEGATIVE = "NEGATIVE"
MISSING = "MISSING"
_OBSERVED_STATES = (POSITIVE, UNCHANGED, NEGATIVE)
_PARTICIPATION_STATES = frozenset((*_OBSERVED_STATES, MISSING))


@dataclass(frozen=True)
class HistoricalEvidenceOutputContract:
    corpus_id: str
    corpus_version: str
    feature_set_version: str
    runtime_version: str
    aggregation_version: str
    breadth_feature_name: str
    breadth_feature_version: str
    leadership_feature_name: str
    leadership_feature_version: str


@dataclass(frozen=True)
class HistoricalMemberEvidence:
    instrument_id: str
    membership_valid_from: date
    membership_valid_to: date | None
    participation_state: str
    observation_date: date | None


@dataclass(frozen=True)
class HistoricalTopicEvidence:
    topic_id: str
    core_members: tuple[HistoricalMemberEvidence, ...]
    leader_instrument_ids: tuple[str, ...]


@dataclass(frozen=True)
class HistoricalEvidenceCase:
    case_id: str
    case_version: str
    as_of: date
    source_data_version: str
    membership_version: str
    leader_set_version: str
    classification_policy_id: str
    classification_policy_version: str
    labels: tuple[str, ...]
    topics: tuple[HistoricalTopicEvidence, ...]

    @property
    def identity(self) -> tuple[str, str]:
        return self.case_id, self.case_version


@dataclass(frozen=True)
class HistoricalEvidenceDataset:
    dataset_id: str
    dataset_version: str
    output: HistoricalEvidenceOutputContract
    source_references: tuple[str, ...]
    cases: tuple[HistoricalEvidenceCase, ...]
    content_digest: str
    mode: str = RESEARCH_ONLY
    schema_version: str = HISTORICAL_EVIDENCE_SCHEMA_VERSION


def load_historical_evidence_dataset(path: str | Path) -> HistoricalEvidenceDataset:
    """Load strict preclassified point-in-time evidence without deriving any state."""

    return parse_historical_evidence_dataset(json.loads(Path(path).read_text(encoding="utf-8")))


def parse_historical_evidence_dataset(document: object) -> HistoricalEvidenceDataset:
    root = _mapping(document, "historical evidence dataset")
    _exact_keys(
        root,
        {
            "schemaVersion",
            "mode",
            "datasetId",
            "datasetVersion",
            "outputContract",
            "sourceReferences",
            "cases",
            "contentDigest",
        },
        "historical evidence dataset",
    )
    if root["schemaVersion"] != HISTORICAL_EVIDENCE_SCHEMA_VERSION:
        raise FormulaResearchValidationError("unsupported historical evidence schema version")
    if root["mode"] != RESEARCH_ONLY:
        raise FormulaResearchValidationError("historical evidence must remain RESEARCH_ONLY")

    output = _parse_output_contract(root["outputContract"])
    sources = _identities(root["sourceReferences"], "sourceReferences")
    if not sources:
        raise FormulaResearchValidationError("sourceReferences must be non-empty")
    case_documents = _sequence(root["cases"], "cases")
    if not case_documents:
        raise FormulaResearchValidationError("historical evidence must contain cases")
    cases = tuple(sorted((_parse_case(item) for item in case_documents), key=lambda x: x.identity))
    identities = tuple(case.identity for case in cases)
    if len(identities) != len(set(identities)):
        raise FormulaResearchValidationError("historical evidence case identities must be unique")

    dataset_id = _identity(root["datasetId"], "datasetId")
    dataset_version = _identity(root["datasetVersion"], "datasetVersion")
    declared_digest = _sha256(root["contentDigest"], "contentDigest")
    digest = _dataset_digest(dataset_id, dataset_version, output, sources, cases)
    if declared_digest != digest:
        raise FormulaResearchValidationError(
            "historical evidence content digest does not match content"
        )
    return HistoricalEvidenceDataset(
        dataset_id,
        dataset_version,
        output,
        sources,
        cases,
        digest,
    )


def export_historical_evidence_dataset(dataset: HistoricalEvidenceDataset) -> str:
    """Export a deterministic dataset after validating its complete identity."""

    _validate_dataset(dataset)
    return _json(_dataset_document(dataset, include_digest=True))


def build_historical_formula_research_corpus(
    dataset: HistoricalEvidenceDataset,
) -> FormulaResearchCorpus:
    """Convert explicit states to counts accepted by the standard replay corpus."""

    _validate_dataset(dataset)
    cases = tuple(
        ResearchCorpusCase(
            case.case_id,
            case.case_version,
            case.labels,
            _build_aggregation(dataset, case),
        )
        for case in dataset.cases
    )
    return create_formula_research_corpus(
        dataset.output.corpus_id,
        dataset.output.corpus_version,
        cases,
    )


def _build_aggregation(
    dataset: HistoricalEvidenceDataset,
    case: HistoricalEvidenceCase,
) -> AggregationResult:
    aggregates = tuple(_build_topic_aggregate(dataset, case, topic) for topic in case.topics)
    return AggregationResult(
        case.as_of,
        dataset.output.feature_set_version,
        dataset.output.runtime_version,
        dataset.output.aggregation_version,
        aggregates,
    )


def _build_topic_aggregate(
    dataset: HistoricalEvidenceDataset,
    case: HistoricalEvidenceCase,
    topic: HistoricalTopicEvidence,
) -> FeatureAggregate:
    members = {member.instrument_id: member for member in topic.core_members}
    breadth = _build_feature(
        dataset,
        case,
        topic.topic_id,
        dataset.output.breadth_feature_name,
        dataset.output.breadth_feature_version,
        topic.core_members,
        "EXPLICIT_CORE",
    )
    leaders = tuple(members[instrument_id] for instrument_id in topic.leader_instrument_ids)
    leadership = _build_feature(
        dataset,
        case,
        topic.topic_id,
        dataset.output.leadership_feature_name,
        dataset.output.leadership_feature_version,
        leaders,
        "EXPLICIT_LEADER_SET",
    )
    features = tuple(sorted((breadth, leadership), key=lambda item: item.feature_name))
    ready = sum(feature.status == FeatureStatus.READY for feature in features)
    insufficient = sum(feature.status == FeatureStatus.DATA_INSUFFICIENT for feature in features)
    coverages = tuple(feature.coverage for feature in features if feature.coverage is not None)
    flags = tuple(sorted({flag for feature in features for flag in feature.quality_flags}))
    status = (
        AggregateStatus.READY_UNSCORED if insufficient == 0 else AggregateStatus.DATA_INSUFFICIENT
    )
    return FeatureAggregate(
        topic.topic_id,
        case.as_of,
        dataset.output.feature_set_version,
        dataset.output.aggregation_version,
        status,
        features,
        QualitySummary(
            ready,
            insufficient,
            0,
            min(coverages) if coverages else None,
            fmean(coverages) if coverages else None,
        ),
        flags,
    )


def _build_feature(
    dataset: HistoricalEvidenceDataset,
    case: HistoricalEvidenceCase,
    topic_id: str,
    feature_name: str,
    feature_version: str,
    members: tuple[HistoricalMemberEvidence, ...],
    population: str,
) -> FeatureResult:
    counts = {state: 0 for state in _OBSERVED_STATES}
    missing_count = 0
    for member in members:
        if member.participation_state == MISSING:
            missing_count += 1
        else:
            counts[member.participation_state] += 1
    observed_count = sum(counts.values())
    declared_count = len(members)
    coverage = observed_count / declared_count if declared_count else None
    flags: list[str] = []
    if declared_count == 0:
        flags.append("NO_EXPLICIT_LEADER_SET")
    elif missing_count:
        flags.append(
            "MISSING_MEMBER_EVIDENCE"
            if population == "EXPLICIT_CORE"
            else "MISSING_LEADER_EVIDENCE"
        )
    ready = observed_count > 0
    value = (
        {
            "positiveCount": counts[POSITIVE],
            "unchangedCount": counts[UNCHANGED],
            "negativeCount": counts[NEGATIVE],
        }
        if ready
        else None
    )
    metadata = tuple(
        sorted(
            (
                ("classificationPolicyId", case.classification_policy_id),
                ("classificationPolicyVersion", case.classification_policy_version),
                ("declaredCount", declared_count),
                ("leaderSetVersion", case.leader_set_version),
                ("membershipVersion", case.membership_version),
                ("missingCount", missing_count),
                ("population", population),
                ("sourceDataVersion", case.source_data_version),
                ("sourceReferences", list(dataset.source_references)),
            )
        )
    )
    return FeatureResult(
        feature_name,
        feature_version,
        topic_id,
        case.as_of,
        FeatureStatus.READY if ready else FeatureStatus.DATA_INSUFFICIENT,
        value,
        coverage,
        tuple(flags),
        metadata,
    )


def _parse_output_contract(value: object) -> HistoricalEvidenceOutputContract:
    item = _mapping(value, "outputContract")
    fields = {
        "corpusId",
        "corpusVersion",
        "featureSetVersion",
        "runtimeVersion",
        "aggregationVersion",
        "breadthFeatureName",
        "breadthFeatureVersion",
        "leadershipFeatureName",
        "leadershipFeatureVersion",
    }
    _exact_keys(item, fields, "outputContract")
    values = {key: _identity(item[key], key) for key in fields}
    if values["breadthFeatureName"] == values["leadershipFeatureName"]:
        raise FormulaResearchValidationError("output feature names must be distinct")
    return HistoricalEvidenceOutputContract(
        values["corpusId"],
        values["corpusVersion"],
        values["featureSetVersion"],
        values["runtimeVersion"],
        values["aggregationVersion"],
        values["breadthFeatureName"],
        values["breadthFeatureVersion"],
        values["leadershipFeatureName"],
        values["leadershipFeatureVersion"],
    )


def _parse_case(value: object) -> HistoricalEvidenceCase:
    item = _mapping(value, "historical evidence case")
    _exact_keys(
        item,
        {
            "caseId",
            "caseVersion",
            "asOf",
            "sourceDataVersion",
            "membershipVersion",
            "leaderSetVersion",
            "classificationPolicyId",
            "classificationPolicyVersion",
            "labels",
            "topics",
        },
        "historical evidence case",
    )
    as_of = _date(item["asOf"], "asOf")
    topic_documents = _sequence(item["topics"], "topics")
    if not topic_documents:
        raise FormulaResearchValidationError("historical evidence case must contain topics")
    topics = tuple(
        sorted((_parse_topic(topic, as_of) for topic in topic_documents), key=lambda x: x.topic_id)
    )
    topic_ids = tuple(topic.topic_id for topic in topics)
    if len(topic_ids) != len(set(topic_ids)):
        raise FormulaResearchValidationError("case topic identities must be unique")
    return HistoricalEvidenceCase(
        _identity(item["caseId"], "caseId"),
        _identity(item["caseVersion"], "caseVersion"),
        as_of,
        _identity(item["sourceDataVersion"], "sourceDataVersion"),
        _identity(item["membershipVersion"], "membershipVersion"),
        _identity(item["leaderSetVersion"], "leaderSetVersion"),
        _identity(item["classificationPolicyId"], "classificationPolicyId"),
        _identity(item["classificationPolicyVersion"], "classificationPolicyVersion"),
        _identities(item["labels"], "labels"),
        topics,
    )


def _parse_topic(value: object, as_of: date) -> HistoricalTopicEvidence:
    item = _mapping(value, "historical topic evidence")
    _exact_keys(
        item,
        {"topicId", "coreMembers", "leaderInstrumentIds"},
        "historical topic evidence",
    )
    members = tuple(
        sorted(
            (
                _parse_member(member, as_of)
                for member in _sequence(item["coreMembers"], "coreMembers")
            ),
            key=lambda member: member.instrument_id,
        )
    )
    if not members:
        raise FormulaResearchValidationError("topic coreMembers must be non-empty")
    member_ids = tuple(member.instrument_id for member in members)
    if len(member_ids) != len(set(member_ids)):
        raise FormulaResearchValidationError("topic core member identities must be unique")
    leaders = _identities(item["leaderInstrumentIds"], "leaderInstrumentIds")
    unknown = set(leaders) - set(member_ids)
    if unknown:
        raise FormulaResearchValidationError("leader identities must be explicit CORE members")
    return HistoricalTopicEvidence(
        _identity(item["topicId"], "topicId"),
        members,
        leaders,
    )


def _parse_member(value: object, as_of: date) -> HistoricalMemberEvidence:
    item = _mapping(value, "historical member evidence")
    _exact_keys(
        item,
        {
            "instrumentId",
            "membershipValidFrom",
            "membershipValidTo",
            "participationState",
            "observationDate",
        },
        "historical member evidence",
    )
    valid_from = _date(item["membershipValidFrom"], "membershipValidFrom")
    valid_to = _optional_date(item["membershipValidTo"], "membershipValidTo")
    if valid_to is not None and valid_to < valid_from:
        raise FormulaResearchValidationError("membership validity interval is inverted")
    if as_of < valid_from or (valid_to is not None and as_of > valid_to):
        raise FormulaResearchValidationError("membership interval does not contain case asOf")
    state = _identity(item["participationState"], "participationState")
    if state not in _PARTICIPATION_STATES:
        raise FormulaResearchValidationError("unsupported participationState")
    observation_date = _optional_date(item["observationDate"], "observationDate")
    if state == MISSING and observation_date is not None:
        raise FormulaResearchValidationError("MISSING evidence cannot have observationDate")
    if state != MISSING and observation_date is None:
        raise FormulaResearchValidationError("observed evidence requires observationDate")
    if observation_date is not None and observation_date > as_of:
        raise FormulaResearchValidationError("observationDate cannot be after case asOf")
    return HistoricalMemberEvidence(
        _identity(item["instrumentId"], "instrumentId"),
        valid_from,
        valid_to,
        state,
        observation_date,
    )


def _validate_dataset(dataset: HistoricalEvidenceDataset) -> None:
    if (
        dataset.mode != RESEARCH_ONLY
        or dataset.schema_version != HISTORICAL_EVIDENCE_SCHEMA_VERSION
    ):
        raise FormulaResearchValidationError("historical evidence identity is not research-only v1")
    digest = _dataset_digest(
        dataset.dataset_id,
        dataset.dataset_version,
        dataset.output,
        dataset.source_references,
        dataset.cases,
    )
    if dataset.content_digest != digest:
        raise FormulaResearchValidationError(
            "historical evidence content digest does not match content"
        )


def _dataset_digest(
    dataset_id: str,
    dataset_version: str,
    output: HistoricalEvidenceOutputContract,
    source_references: tuple[str, ...],
    cases: tuple[HistoricalEvidenceCase, ...],
) -> str:
    dataset = HistoricalEvidenceDataset(
        dataset_id,
        dataset_version,
        output,
        source_references,
        cases,
        content_digest="",
    )
    return hashlib.sha256(
        _json(_dataset_document(dataset, include_digest=False)).encode()
    ).hexdigest()


def _dataset_document(
    dataset: HistoricalEvidenceDataset, *, include_digest: bool
) -> dict[str, object]:
    document: dict[str, object] = {
        "schemaVersion": dataset.schema_version,
        "mode": dataset.mode,
        "datasetId": dataset.dataset_id,
        "datasetVersion": dataset.dataset_version,
        "outputContract": _output_document(dataset.output),
        "sourceReferences": list(dataset.source_references),
        "cases": [_case_document(case) for case in dataset.cases],
    }
    if include_digest:
        document["contentDigest"] = dataset.content_digest
    return document


def _output_document(output: HistoricalEvidenceOutputContract) -> dict[str, str]:
    return {
        "corpusId": output.corpus_id,
        "corpusVersion": output.corpus_version,
        "featureSetVersion": output.feature_set_version,
        "runtimeVersion": output.runtime_version,
        "aggregationVersion": output.aggregation_version,
        "breadthFeatureName": output.breadth_feature_name,
        "breadthFeatureVersion": output.breadth_feature_version,
        "leadershipFeatureName": output.leadership_feature_name,
        "leadershipFeatureVersion": output.leadership_feature_version,
    }


def _case_document(case: HistoricalEvidenceCase) -> dict[str, object]:
    return {
        "caseId": case.case_id,
        "caseVersion": case.case_version,
        "asOf": case.as_of.isoformat(),
        "sourceDataVersion": case.source_data_version,
        "membershipVersion": case.membership_version,
        "leaderSetVersion": case.leader_set_version,
        "classificationPolicyId": case.classification_policy_id,
        "classificationPolicyVersion": case.classification_policy_version,
        "labels": list(case.labels),
        "topics": [_topic_document(topic) for topic in case.topics],
    }


def _topic_document(topic: HistoricalTopicEvidence) -> dict[str, object]:
    return {
        "topicId": topic.topic_id,
        "coreMembers": [_member_document(member) for member in topic.core_members],
        "leaderInstrumentIds": list(topic.leader_instrument_ids),
    }


def _member_document(member: HistoricalMemberEvidence) -> dict[str, object]:
    return {
        "instrumentId": member.instrument_id,
        "membershipValidFrom": member.membership_valid_from.isoformat(),
        "membershipValidTo": (
            member.membership_valid_to.isoformat()
            if member.membership_valid_to is not None
            else None
        ),
        "participationState": member.participation_state,
        "observationDate": (
            member.observation_date.isoformat() if member.observation_date is not None else None
        ),
    }


def _mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise FormulaResearchValidationError(f"{label} must be a JSON object")
    return value


def _sequence(value: object, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise FormulaResearchValidationError(f"{label} must be a JSON array")
    return value


def _exact_keys(value: Mapping[str, Any], expected: set[str], label: str) -> None:
    if set(value) != expected:
        raise FormulaResearchValidationError(f"{label} has unexpected or missing fields")


def _identity(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise FormulaResearchValidationError(f"{label} must be a trimmed non-empty string")
    return value


def _identities(value: object, label: str) -> tuple[str, ...]:
    identities = tuple(sorted(_identity(item, label) for item in _sequence(value, label)))
    if len(identities) != len(set(identities)):
        raise FormulaResearchValidationError(f"{label} must contain unique identities")
    return identities


def _date(value: object, label: str) -> date:
    if not isinstance(value, str):
        raise FormulaResearchValidationError(f"{label} must be an ISO date")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise FormulaResearchValidationError(f"{label} must be an ISO date") from exc
    if parsed.isoformat() != value:
        raise FormulaResearchValidationError(f"{label} must be a canonical ISO date")
    return parsed


def _optional_date(value: object, label: str) -> date | None:
    return None if value is None else _date(value, label)


def _sha256(value: object, label: str) -> str:
    text = _identity(value, label)
    if len(text) != 64 or any(character not in "0123456789abcdef" for character in text):
        raise FormulaResearchValidationError(f"{label} must be a lowercase SHA-256 digest")
    return text


def _json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


__all__ = [
    "HISTORICAL_EVIDENCE_SCHEMA_VERSION",
    "MISSING",
    "NEGATIVE",
    "POSITIVE",
    "UNCHANGED",
    "HistoricalEvidenceCase",
    "HistoricalEvidenceDataset",
    "HistoricalEvidenceOutputContract",
    "HistoricalMemberEvidence",
    "HistoricalTopicEvidence",
    "build_historical_formula_research_corpus",
    "export_historical_evidence_dataset",
    "load_historical_evidence_dataset",
    "parse_historical_evidence_dataset",
]
