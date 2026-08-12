"""Deterministic, public-safe replay corpus for research-only Topic Formula runs."""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from statistics import fmean
from typing import Any

from .aggregation import AggregateStatus, AggregationResult, FeatureAggregate, QualitySummary
from .features.contracts import FeatureResult, FeatureStatus
from .research import (
    RESEARCH_ONLY,
    FormulaResearchResult,
    FormulaResearchValidationError,
    ResearchCandidate,
    run_formula_research,
)

CORPUS_SCHEMA_VERSION = "topic-formula-replay-corpus.v1"
CORPUS_RUN_SCHEMA_VERSION = "topic-formula-replay-corpus-run.v1"
_AGGREGATE_STATUSES = {
    AggregateStatus.INVALID_INPUT,
    AggregateStatus.DATA_INSUFFICIENT,
    AggregateStatus.READY_UNSCORED,
}
_FEATURE_STATUSES = {
    FeatureStatus.READY,
    FeatureStatus.DATA_INSUFFICIENT,
    FeatureStatus.INVALID_INPUT,
}
_FORBIDDEN_PUBLIC_KEY_FRAGMENTS = (
    "apikey",
    "credential",
    "holding",
    "newstext",
    "password",
    "privateurl",
    "secret",
    "token",
)


@dataclass(frozen=True)
class ResearchCorpusCase:
    case_id: str
    case_version: str
    labels: tuple[str, ...]
    aggregates: AggregationResult

    @property
    def identity(self) -> tuple[str, str]:
        return self.case_id, self.case_version


@dataclass(frozen=True)
class FormulaResearchCorpus:
    corpus_id: str
    corpus_version: str
    cases: tuple[ResearchCorpusCase, ...]
    content_digest: str
    mode: str = RESEARCH_ONLY
    schema_version: str = CORPUS_SCHEMA_VERSION


@dataclass(frozen=True)
class CorpusCaseResearchResult:
    case_id: str
    case_version: str
    result: FormulaResearchResult


@dataclass(frozen=True)
class FormulaResearchCorpusRun:
    corpus_id: str
    corpus_version: str
    corpus_content_digest: str
    research_runtime_version: str
    candidate_identities: tuple[tuple[str, str], ...]
    case_results: tuple[CorpusCaseResearchResult, ...]
    run_digest: str
    mode: str = RESEARCH_ONLY
    schema_version: str = CORPUS_RUN_SCHEMA_VERSION


def load_formula_research_corpus(path: str | Path) -> FormulaResearchCorpus:
    """Load and validate a synthetic replay corpus from a UTF-8 JSON document."""

    document = json.loads(Path(path).read_text(encoding="utf-8"))
    return parse_formula_research_corpus(document)


def parse_formula_research_corpus(document: object) -> FormulaResearchCorpus:
    """Parse a corpus document and reject malformed, unsafe, or tampered evidence."""

    root = _mapping(document, "corpus document")
    _exact_keys(
        root,
        {
            "schemaVersion",
            "mode",
            "corpusId",
            "corpusVersion",
            "contentDigest",
            "cases",
        },
        "corpus document",
    )
    if root["schemaVersion"] != CORPUS_SCHEMA_VERSION:
        raise FormulaResearchValidationError("unsupported replay corpus schema version")
    if root["mode"] != RESEARCH_ONLY:
        raise FormulaResearchValidationError("replay corpus must remain RESEARCH_ONLY")
    corpus_id = _identity(root["corpusId"], "corpusId")
    corpus_version = _identity(root["corpusVersion"], "corpusVersion")
    declared_digest = _sha256(root["contentDigest"], "contentDigest")
    case_documents = _sequence(root["cases"], "cases")
    if not case_documents:
        raise FormulaResearchValidationError("replay corpus must contain at least one case")
    cases = tuple(sorted((_parse_case(item) for item in case_documents), key=lambda x: x.identity))
    identities = tuple(case.identity for case in cases)
    if len(identities) != len(set(identities)):
        raise FormulaResearchValidationError("replay corpus case identities must be unique")
    calculated_digest = _corpus_digest(corpus_id, corpus_version, cases)
    if declared_digest != calculated_digest:
        raise FormulaResearchValidationError("replay corpus content digest does not match content")
    return FormulaResearchCorpus(corpus_id, corpus_version, cases, calculated_digest)


def export_formula_research_corpus(corpus: FormulaResearchCorpus) -> str:
    """Export the complete corpus deterministically after revalidating its identity."""

    _validate_corpus(corpus)
    return _json(_corpus_document(corpus, include_digest=True))


def create_formula_research_corpus(
    corpus_id: str,
    corpus_version: str,
    cases: Sequence[ResearchCorpusCase],
) -> FormulaResearchCorpus:
    """Create a canonical corpus from validated in-memory cases."""

    normalized_id = _identity(corpus_id, "corpusId")
    normalized_version = _identity(corpus_version, "corpusVersion")
    ordered = tuple(sorted(cases, key=lambda item: item.identity))
    if not ordered:
        raise FormulaResearchValidationError("replay corpus must contain at least one case")
    identities = tuple(case.identity for case in ordered)
    if len(identities) != len(set(identities)):
        raise FormulaResearchValidationError("replay corpus case identities must be unique")
    corpus = FormulaResearchCorpus(
        normalized_id,
        normalized_version,
        ordered,
        _corpus_digest(normalized_id, normalized_version, ordered),
    )
    _validate_corpus(corpus)
    return corpus


def run_formula_research_corpus(
    corpus: FormulaResearchCorpus,
    candidates: Sequence[ResearchCandidate],
    *,
    research_runtime_version: str,
) -> FormulaResearchCorpusRun:
    """Run the same research-only candidates over every immutable corpus case."""

    _validate_corpus(corpus)
    case_results = tuple(
        CorpusCaseResearchResult(
            case.case_id,
            case.case_version,
            run_formula_research(
                case.aggregates,
                candidates,
                research_runtime_version=research_runtime_version,
            ),
        )
        for case in corpus.cases
    )
    candidate_identities = tuple(
        (item.candidate_id, item.candidate_version)
        for item in case_results[0].result.candidate_results
    )
    for item in case_results:
        current = tuple(
            (candidate.candidate_id, candidate.candidate_version)
            for candidate in item.result.candidate_results
        )
        if current != candidate_identities:
            raise FormulaResearchValidationError(
                "corpus cases must retain one canonical candidate set"
            )
    draft = FormulaResearchCorpusRun(
        corpus.corpus_id,
        corpus.corpus_version,
        corpus.content_digest,
        research_runtime_version,
        candidate_identities,
        case_results,
        run_digest="",
    )
    digest = hashlib.sha256(
        _json(_corpus_run_document(draft, include_digest=False)).encode()
    ).hexdigest()
    return FormulaResearchCorpusRun(
        draft.corpus_id,
        draft.corpus_version,
        draft.corpus_content_digest,
        draft.research_runtime_version,
        draft.candidate_identities,
        draft.case_results,
        digest,
    )


def export_formula_research_corpus_run(run: FormulaResearchCorpusRun) -> str:
    """Export a deterministic lineage manifest without embedding callable candidates."""

    if run.mode != RESEARCH_ONLY:
        raise FormulaResearchValidationError("corpus run must remain RESEARCH_ONLY")
    expected = hashlib.sha256(
        _json(_corpus_run_document(run, include_digest=False)).encode()
    ).hexdigest()
    if run.run_digest != expected:
        raise FormulaResearchValidationError("corpus run digest does not match content")
    return _json(_corpus_run_document(run, include_digest=True))


def _parse_case(value: object) -> ResearchCorpusCase:
    item = _mapping(value, "case")
    _exact_keys(item, {"caseId", "caseVersion", "labels", "aggregation"}, "case")
    case_id = _identity(item["caseId"], "caseId")
    case_version = _identity(item["caseVersion"], "caseVersion")
    labels = tuple(
        sorted(_identity(label, "case label") for label in _sequence(item["labels"], "labels"))
    )
    if len(labels) != len(set(labels)):
        raise FormulaResearchValidationError("case labels must be unique")
    return ResearchCorpusCase(
        case_id, case_version, labels, _parse_aggregation(item["aggregation"])
    )


def _parse_aggregation(value: object) -> AggregationResult:
    item = _mapping(value, "aggregation")
    _exact_keys(
        item,
        {"asOf", "featureSetVersion", "runtimeVersion", "aggregationVersion", "topics"},
        "aggregation",
    )
    try:
        as_of = date.fromisoformat(_identity(item["asOf"], "asOf"))
    except ValueError as exc:
        raise FormulaResearchValidationError("asOf must be an ISO date") from exc
    feature_set_version = _identity(item["featureSetVersion"], "featureSetVersion")
    runtime_version = _identity(item["runtimeVersion"], "runtimeVersion")
    aggregation_version = _identity(item["aggregationVersion"], "aggregationVersion")
    topics = tuple(
        sorted(
            (
                _parse_topic(
                    topic,
                    as_of=as_of,
                    feature_set_version=feature_set_version,
                    aggregation_version=aggregation_version,
                )
                for topic in _sequence(item["topics"], "topics")
            ),
            key=lambda topic: topic.topic_id,
        )
    )
    if not topics:
        raise FormulaResearchValidationError("aggregation must contain at least one topic")
    topic_ids = tuple(topic.topic_id for topic in topics)
    if len(topic_ids) != len(set(topic_ids)):
        raise FormulaResearchValidationError("aggregation topic identities must be unique")
    return AggregationResult(
        as_of,
        feature_set_version,
        runtime_version,
        aggregation_version,
        topics,
    )


def _parse_topic(
    value: object,
    *,
    as_of: date,
    feature_set_version: str,
    aggregation_version: str,
) -> FeatureAggregate:
    item = _mapping(value, "topic aggregate")
    _exact_keys(
        item,
        {"topicId", "status", "quality", "qualityFlags", "features"},
        "topic aggregate",
    )
    topic_id = _identity(item["topicId"], "topicId")
    status = _identity(item["status"], "aggregate status")
    if status not in _AGGREGATE_STATUSES:
        raise FormulaResearchValidationError(f"unsupported aggregate status: {status}")
    features = tuple(
        sorted(
            (
                _parse_feature(feature, topic_id=topic_id, as_of=as_of)
                for feature in _sequence(item["features"], "features")
            ),
            key=lambda feature: (feature.feature_name, feature.feature_version),
        )
    )
    if not features:
        raise FormulaResearchValidationError("topic aggregate must contain features")
    identities = tuple((feature.feature_name, feature.feature_version) for feature in features)
    if len(identities) != len(set(identities)):
        raise FormulaResearchValidationError("topic feature identities must be unique")
    quality = _parse_quality(item["quality"])
    _validate_quality(quality, features)
    quality_flags = tuple(
        sorted(
            _identity(flag, "quality flag")
            for flag in _sequence(item["qualityFlags"], "qualityFlags")
        )
    )
    if len(quality_flags) != len(set(quality_flags)):
        raise FormulaResearchValidationError("aggregate quality flags must be unique")
    expected_flags = tuple(sorted({flag for feature in features for flag in feature.quality_flags}))
    if quality_flags != expected_flags:
        raise FormulaResearchValidationError(
            "aggregate quality flags must equal the canonical feature flag union"
        )
    return FeatureAggregate(
        topic_id,
        as_of,
        feature_set_version,
        aggregation_version,
        status,
        features,
        quality,
        quality_flags,
    )


def _parse_feature(value: object, *, topic_id: str, as_of: date) -> FeatureResult:
    item = _mapping(value, "feature")
    _exact_keys(
        item,
        {
            "featureName",
            "featureVersion",
            "status",
            "value",
            "coverage",
            "qualityFlags",
            "metadata",
        },
        "feature",
    )
    feature_name = _identity(item["featureName"], "featureName")
    feature_version = _identity(item["featureVersion"], "featureVersion")
    status = _identity(item["status"], "feature status")
    if status not in _FEATURE_STATUSES:
        raise FormulaResearchValidationError(f"unsupported feature status: {status}")
    feature_value = item["value"]
    if feature_value is not None and (
        isinstance(feature_value, bool) or not isinstance(feature_value, (int, float, dict))
    ):
        raise FormulaResearchValidationError("feature value must be numeric, object, or null")
    _validate_public_json(feature_value, "feature value")
    coverage = _nullable_number(item["coverage"], "coverage")
    if coverage is not None and not 0.0 <= coverage <= 1.0:
        raise FormulaResearchValidationError("coverage must be between zero and one")
    quality_flags = tuple(
        sorted(
            _identity(flag, "quality flag")
            for flag in _sequence(item["qualityFlags"], "qualityFlags")
        )
    )
    if len(quality_flags) != len(set(quality_flags)):
        raise FormulaResearchValidationError("feature quality flags must be unique")
    metadata = _mapping(item["metadata"], "metadata")
    _validate_public_json(metadata, "metadata")
    return FeatureResult(
        feature_name,
        feature_version,
        topic_id,
        as_of,
        status,
        feature_value,
        coverage,
        quality_flags,
        tuple(sorted(metadata.items())),
    )


def _parse_quality(value: object) -> QualitySummary:
    item = _mapping(value, "quality")
    _exact_keys(
        item,
        {
            "readyFeatureCount",
            "insufficientFeatureCount",
            "invalidFeatureCount",
            "coverageMin",
            "coverageMean",
        },
        "quality",
    )
    return QualitySummary(
        _non_negative_integer(item["readyFeatureCount"], "readyFeatureCount"),
        _non_negative_integer(item["insufficientFeatureCount"], "insufficientFeatureCount"),
        _non_negative_integer(item["invalidFeatureCount"], "invalidFeatureCount"),
        _nullable_number(item["coverageMin"], "coverageMin"),
        _nullable_number(item["coverageMean"], "coverageMean"),
    )


def _validate_quality(quality: QualitySummary, features: tuple[FeatureResult, ...]) -> None:
    counts = Counter(feature.status for feature in features)
    if (
        quality.ready_feature_count != counts[FeatureStatus.READY]
        or quality.insufficient_feature_count != counts[FeatureStatus.DATA_INSUFFICIENT]
        or quality.invalid_feature_count != counts[FeatureStatus.INVALID_INPUT]
    ):
        raise FormulaResearchValidationError("quality feature counts do not match features")
    coverages = tuple(feature.coverage for feature in features if feature.coverage is not None)
    expected_min = min(coverages) if coverages else None
    expected_mean = fmean(coverages) if coverages else None
    if not _same_optional_number(quality.coverage_min, expected_min):
        raise FormulaResearchValidationError("quality coverageMin does not match features")
    if not _same_optional_number(quality.coverage_mean, expected_mean):
        raise FormulaResearchValidationError("quality coverageMean does not match features")


def _validate_corpus(corpus: FormulaResearchCorpus) -> None:
    if corpus.mode != RESEARCH_ONLY or corpus.schema_version != CORPUS_SCHEMA_VERSION:
        raise FormulaResearchValidationError("corpus identity is not research-only v1")
    expected = _corpus_digest(corpus.corpus_id, corpus.corpus_version, corpus.cases)
    if corpus.content_digest != expected:
        raise FormulaResearchValidationError("replay corpus digest does not match content")


def _corpus_digest(
    corpus_id: str, corpus_version: str, cases: tuple[ResearchCorpusCase, ...]
) -> str:
    payload = {
        "schemaVersion": CORPUS_SCHEMA_VERSION,
        "mode": RESEARCH_ONLY,
        "corpusId": corpus_id,
        "corpusVersion": corpus_version,
        "cases": [_case_document(case) for case in cases],
    }
    return hashlib.sha256(_json(payload).encode()).hexdigest()


def _corpus_document(corpus: FormulaResearchCorpus, *, include_digest: bool) -> dict[str, object]:
    document: dict[str, object] = {
        "schemaVersion": corpus.schema_version,
        "mode": corpus.mode,
        "corpusId": corpus.corpus_id,
        "corpusVersion": corpus.corpus_version,
        "cases": [_case_document(case) for case in corpus.cases],
    }
    if include_digest:
        document["contentDigest"] = corpus.content_digest
    return document


def _case_document(case: ResearchCorpusCase) -> dict[str, object]:
    return {
        "caseId": case.case_id,
        "caseVersion": case.case_version,
        "labels": list(case.labels),
        "aggregation": {
            "asOf": case.aggregates.as_of.isoformat(),
            "featureSetVersion": case.aggregates.feature_set_version,
            "runtimeVersion": case.aggregates.runtime_version,
            "aggregationVersion": case.aggregates.aggregation_version,
            "topics": [_topic_document(topic) for topic in case.aggregates.aggregates],
        },
    }


def _topic_document(topic: FeatureAggregate) -> dict[str, object]:
    return {
        "topicId": topic.topic_id,
        "status": topic.status,
        "quality": {
            "readyFeatureCount": topic.quality.ready_feature_count,
            "insufficientFeatureCount": topic.quality.insufficient_feature_count,
            "invalidFeatureCount": topic.quality.invalid_feature_count,
            "coverageMin": topic.quality.coverage_min,
            "coverageMean": topic.quality.coverage_mean,
        },
        "qualityFlags": list(topic.quality_flags),
        "features": [
            {
                "featureName": feature.feature_name,
                "featureVersion": feature.feature_version,
                "status": feature.status,
                "value": feature.value,
                "coverage": feature.coverage,
                "qualityFlags": list(feature.quality_flags),
                "metadata": dict(feature.metadata),
            }
            for feature in topic.feature_results
        ],
    }


def _corpus_run_document(
    run: FormulaResearchCorpusRun, *, include_digest: bool
) -> dict[str, object]:
    document: dict[str, object] = {
        "schemaVersion": run.schema_version,
        "mode": run.mode,
        "corpusId": run.corpus_id,
        "corpusVersion": run.corpus_version,
        "corpusContentDigest": run.corpus_content_digest,
        "researchRuntimeVersion": run.research_runtime_version,
        "candidateIdentities": [list(identity) for identity in run.candidate_identities],
        "cases": [
            {
                "caseId": item.case_id,
                "caseVersion": item.case_version,
                "asOf": item.result.as_of.isoformat(),
                "replayDigest": item.result.replay_digest,
            }
            for item in run.case_results
        ],
    }
    if include_digest:
        document["runDigest"] = run.run_digest
    return document


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
        raise FormulaResearchValidationError(f"{label} fields do not match the corpus contract")


def _identity(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise FormulaResearchValidationError(f"{label} must be a trimmed non-empty string")
    return value


def _sha256(value: object, label: str) -> str:
    text = _identity(value, label)
    if len(text) != 64:
        raise FormulaResearchValidationError(f"{label} must be SHA-256")
    try:
        int(text, 16)
    except ValueError as exc:
        raise FormulaResearchValidationError(f"{label} must be hexadecimal") from exc
    return text


def _non_negative_integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise FormulaResearchValidationError(f"{label} must be a non-negative integer")
    return value


def _nullable_number(value: object, label: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise FormulaResearchValidationError(f"{label} must be numeric or null")
    number = float(value)
    if not math.isfinite(number):
        raise FormulaResearchValidationError(f"{label} must be finite")
    return number


def _same_optional_number(left: float | None, right: float | None) -> bool:
    if left is None or right is None:
        return left is right
    return math.isclose(left, right, rel_tol=0.0, abs_tol=1e-12)


def _validate_public_json(value: object, label: str) -> None:
    if value is None or isinstance(value, (bool, str)):
        return
    if isinstance(value, (int, float)):
        if isinstance(value, float) and not math.isfinite(value):
            raise FormulaResearchValidationError(f"{label} contains a non-finite number")
        return
    if isinstance(value, list):
        for item in value:
            _validate_public_json(item, label)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise FormulaResearchValidationError(f"{label} keys must be strings")
            normalized = "".join(character for character in key.lower() if character.isalnum())
            if any(fragment in normalized for fragment in _FORBIDDEN_PUBLIC_KEY_FRAGMENTS):
                raise FormulaResearchValidationError(f"{label} contains a forbidden public key")
            _validate_public_json(item, label)
        return
    raise FormulaResearchValidationError(f"{label} must contain only JSON-safe values")


def _json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


__all__ = [
    "CORPUS_RUN_SCHEMA_VERSION",
    "CORPUS_SCHEMA_VERSION",
    "CorpusCaseResearchResult",
    "FormulaResearchCorpus",
    "FormulaResearchCorpusRun",
    "ResearchCorpusCase",
    "create_formula_research_corpus",
    "export_formula_research_corpus",
    "export_formula_research_corpus_run",
    "load_formula_research_corpus",
    "parse_formula_research_corpus",
    "run_formula_research_corpus",
]
