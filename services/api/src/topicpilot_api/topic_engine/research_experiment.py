"""Deterministic manifest and report for public-safe Topic Formula experiments."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

from .research import RESEARCH_ONLY, FormulaResearchValidationError
from .research_analysis import (
    FormulaResearchAnalysis,
    analyze_formula_research,
    export_formula_research_analysis,
)
from .research_corpus import (
    FormulaResearchCorpus,
    FormulaResearchCorpusRun,
    export_formula_research_corpus_run,
    load_formula_research_corpus,
    run_formula_research_corpus,
)
from .research_policies import (
    WEIGHTED_ARITHMETIC,
    ParticipationResearchSpec,
    build_participation_research_candidate,
)

EXPERIMENT_SCHEMA_VERSION = "topic-formula-research-experiment.v1"
EXPERIMENT_REPORT_SCHEMA_VERSION = "topic-formula-research-experiment-report.v1"


@dataclass(frozen=True)
class FormulaResearchExperiment:
    experiment_id: str
    experiment_version: str
    research_runtime_version: str
    analysis_runtime_version: str
    corpus_file: str
    corpus: FormulaResearchCorpus
    candidate_specs: tuple[ParticipationResearchSpec, ...]
    manifest_digest: str
    mode: str = RESEARCH_ONLY
    schema_version: str = EXPERIMENT_SCHEMA_VERSION


@dataclass(frozen=True)
class ExperimentCaseAnalysis:
    case_id: str
    case_version: str
    analysis: FormulaResearchAnalysis


@dataclass(frozen=True)
class FormulaResearchExperimentResult:
    experiment_id: str
    experiment_version: str
    manifest_digest: str
    corpus_run: FormulaResearchCorpusRun
    case_analyses: tuple[ExperimentCaseAnalysis, ...]
    experiment_digest: str
    mode: str = RESEARCH_ONLY
    schema_version: str = EXPERIMENT_REPORT_SCHEMA_VERSION


def load_formula_research_experiment(path: str | Path) -> FormulaResearchExperiment:
    """Load a strict experiment manifest and its safe relative replay corpus."""

    manifest_path = Path(path).resolve()
    document = json.loads(manifest_path.read_text(encoding="utf-8"))
    parsed = _parse_manifest(document)
    corpus_path = (manifest_path.parent / PurePosixPath(parsed["corpus_file"])).resolve()
    if not corpus_path.is_relative_to(manifest_path.parent):
        raise FormulaResearchValidationError("experiment corpus path escapes manifest directory")
    corpus = load_formula_research_corpus(corpus_path)
    if corpus.content_digest != parsed["corpus_content_digest"]:
        raise FormulaResearchValidationError("experiment corpus digest does not match manifest")
    return FormulaResearchExperiment(
        parsed["experiment_id"],
        parsed["experiment_version"],
        parsed["research_runtime_version"],
        parsed["analysis_runtime_version"],
        parsed["corpus_file"],
        corpus,
        parsed["candidate_specs"],
        parsed["manifest_digest"],
    )


def export_formula_research_experiment_manifest(
    experiment: FormulaResearchExperiment,
) -> str:
    """Export the canonical manifest without candidate callables."""

    _validate_experiment(experiment)
    return _json(_manifest_document(experiment, include_digest=True))


def run_formula_research_experiment(
    experiment: FormulaResearchExperiment,
) -> FormulaResearchExperimentResult:
    """Execute and analyze every case without ranking or selecting candidates."""

    _validate_experiment(experiment)
    candidates = tuple(
        build_participation_research_candidate(spec) for spec in experiment.candidate_specs
    )
    corpus_run = run_formula_research_corpus(
        experiment.corpus,
        candidates,
        research_runtime_version=experiment.research_runtime_version,
    )
    analyses = tuple(
        ExperimentCaseAnalysis(
            item.case_id,
            item.case_version,
            analyze_formula_research(
                item.result,
                analysis_runtime_version=experiment.analysis_runtime_version,
            ),
        )
        for item in corpus_run.case_results
    )
    draft = FormulaResearchExperimentResult(
        experiment.experiment_id,
        experiment.experiment_version,
        experiment.manifest_digest,
        corpus_run,
        analyses,
        experiment_digest="",
    )
    digest = hashlib.sha256(
        _json(_report_document(draft, include_digest=False)).encode()
    ).hexdigest()
    return FormulaResearchExperimentResult(
        draft.experiment_id,
        draft.experiment_version,
        draft.manifest_digest,
        draft.corpus_run,
        draft.case_analyses,
        digest,
    )


def export_formula_research_experiment_report(
    result: FormulaResearchExperimentResult,
) -> str:
    """Export a deterministic integrated report after validating all lineage."""

    if result.mode != RESEARCH_ONLY:
        raise FormulaResearchValidationError("experiment result must remain RESEARCH_ONLY")
    if result.schema_version != EXPERIMENT_REPORT_SCHEMA_VERSION:
        raise FormulaResearchValidationError("unsupported experiment report schema version")
    expected = hashlib.sha256(
        _json(_report_document(result, include_digest=False)).encode()
    ).hexdigest()
    if result.experiment_digest != expected:
        raise FormulaResearchValidationError("experiment report digest does not match content")
    return _json(_report_document(result, include_digest=True))


def _parse_manifest(document: object) -> dict[str, Any]:
    root = _mapping(document, "experiment manifest")
    _exact_keys(
        root,
        {
            "schemaVersion",
            "mode",
            "experimentId",
            "experimentVersion",
            "researchRuntimeVersion",
            "analysisRuntimeVersion",
            "corpus",
            "candidates",
            "manifestDigest",
        },
        "experiment manifest",
    )
    if root["schemaVersion"] != EXPERIMENT_SCHEMA_VERSION:
        raise FormulaResearchValidationError("unsupported experiment schema version")
    if root["mode"] != RESEARCH_ONLY:
        raise FormulaResearchValidationError("experiment must remain RESEARCH_ONLY")
    corpus_document = _mapping(root["corpus"], "experiment corpus reference")
    _exact_keys(corpus_document, {"file", "contentDigest"}, "experiment corpus reference")
    corpus_file = _safe_relative_file(corpus_document["file"])
    corpus_content_digest = _sha256(corpus_document["contentDigest"], "corpus content digest")
    candidate_documents = _sequence(root["candidates"], "candidates")
    if not candidate_documents:
        raise FormulaResearchValidationError("experiment must contain candidates")
    candidate_specs = tuple(
        sorted(
            (_parse_candidate(item) for item in candidate_documents),
            key=lambda spec: (spec.candidate_id, spec.candidate_version),
        )
    )
    identities = tuple((spec.candidate_id, spec.candidate_version) for spec in candidate_specs)
    if len(identities) != len(set(identities)):
        raise FormulaResearchValidationError("experiment candidate identities must be unique")
    values = {
        "experiment_id": _identity(root["experimentId"], "experimentId"),
        "experiment_version": _identity(root["experimentVersion"], "experimentVersion"),
        "research_runtime_version": _identity(
            root["researchRuntimeVersion"], "researchRuntimeVersion"
        ),
        "analysis_runtime_version": _identity(
            root["analysisRuntimeVersion"], "analysisRuntimeVersion"
        ),
        "corpus_file": corpus_file,
        "corpus_content_digest": corpus_content_digest,
        "candidate_specs": candidate_specs,
        "manifest_digest": _sha256(root["manifestDigest"], "manifestDigest"),
    }
    expected = _manifest_digest(values)
    if values["manifest_digest"] != expected:
        raise FormulaResearchValidationError("experiment manifest digest does not match content")
    return values


def _parse_candidate(value: object) -> ParticipationResearchSpec:
    item = _mapping(value, "experiment candidate")
    _exact_keys(
        item,
        {
            "candidateId",
            "candidateVersion",
            "scorerRuntimeVersion",
            "aggregationMethod",
            "breadth",
            "leadership",
            "sourceReferences",
        },
        "experiment candidate",
    )
    if item["aggregationMethod"] != WEIGHTED_ARITHMETIC:
        raise FormulaResearchValidationError("unsupported experiment aggregation method")
    breadth = _component_spec(item["breadth"], "breadth")
    leadership = _component_spec(item["leadership"], "leadership")
    sources = tuple(
        sorted(
            _identity(source, "source reference")
            for source in _sequence(item["sourceReferences"], "sourceReferences")
        )
    )
    return ParticipationResearchSpec(
        _identity(item["candidateId"], "candidateId"),
        _identity(item["candidateVersion"], "candidateVersion"),
        _identity(item["scorerRuntimeVersion"], "scorerRuntimeVersion"),
        breadth["feature_name"],
        breadth["feature_version"],
        breadth["method"],
        breadth["weight"],
        leadership["feature_name"],
        leadership["feature_version"],
        leadership["method"],
        leadership["weight"],
        sources,
    )


def _component_spec(value: object, label: str) -> dict[str, Any]:
    item = _mapping(value, f"{label} specification")
    _exact_keys(
        item,
        {"featureName", "featureVersion", "method", "weight"},
        f"{label} specification",
    )
    return {
        "feature_name": _identity(item["featureName"], f"{label} featureName"),
        "feature_version": _identity(item["featureVersion"], f"{label} featureVersion"),
        "method": _identity(item["method"], f"{label} method"),
        "weight": _number(item["weight"], f"{label} weight"),
    }


def _validate_experiment(experiment: FormulaResearchExperiment) -> None:
    if experiment.mode != RESEARCH_ONLY or experiment.schema_version != EXPERIMENT_SCHEMA_VERSION:
        raise FormulaResearchValidationError("experiment identity is not research-only v1")
    values = {
        "experiment_id": experiment.experiment_id,
        "experiment_version": experiment.experiment_version,
        "research_runtime_version": experiment.research_runtime_version,
        "analysis_runtime_version": experiment.analysis_runtime_version,
        "corpus_file": experiment.corpus_file,
        "corpus_content_digest": experiment.corpus.content_digest,
        "candidate_specs": experiment.candidate_specs,
    }
    if experiment.manifest_digest != _manifest_digest(values):
        raise FormulaResearchValidationError("experiment manifest digest does not match content")


def _manifest_digest(values: Mapping[str, Any]) -> str:
    return hashlib.sha256(_json(_manifest_payload(values)).encode()).hexdigest()


def _manifest_payload(values: Mapping[str, Any]) -> dict[str, object]:
    return {
        "schemaVersion": EXPERIMENT_SCHEMA_VERSION,
        "mode": RESEARCH_ONLY,
        "experimentId": values["experiment_id"],
        "experimentVersion": values["experiment_version"],
        "researchRuntimeVersion": values["research_runtime_version"],
        "analysisRuntimeVersion": values["analysis_runtime_version"],
        "corpus": {
            "file": values["corpus_file"],
            "contentDigest": values["corpus_content_digest"],
        },
        "candidates": [_candidate_document(spec) for spec in values["candidate_specs"]],
    }


def _manifest_document(
    experiment: FormulaResearchExperiment, *, include_digest: bool
) -> dict[str, object]:
    values = {
        "experiment_id": experiment.experiment_id,
        "experiment_version": experiment.experiment_version,
        "research_runtime_version": experiment.research_runtime_version,
        "analysis_runtime_version": experiment.analysis_runtime_version,
        "corpus_file": experiment.corpus_file,
        "corpus_content_digest": experiment.corpus.content_digest,
        "candidate_specs": experiment.candidate_specs,
    }
    document = _manifest_payload(values)
    if include_digest:
        document["manifestDigest"] = experiment.manifest_digest
    return document


def _candidate_document(spec: ParticipationResearchSpec) -> dict[str, object]:
    return {
        "candidateId": spec.candidate_id,
        "candidateVersion": spec.candidate_version,
        "scorerRuntimeVersion": spec.scorer_runtime_version,
        "aggregationMethod": WEIGHTED_ARITHMETIC,
        "breadth": {
            "featureName": spec.breadth_feature_name,
            "featureVersion": spec.breadth_feature_version,
            "method": spec.breadth_method,
            "weight": spec.breadth_weight,
        },
        "leadership": {
            "featureName": spec.leadership_feature_name,
            "featureVersion": spec.leadership_feature_version,
            "method": spec.leadership_method,
            "weight": spec.leadership_weight,
        },
        "sourceReferences": list(spec.source_references),
    }


def _report_document(
    result: FormulaResearchExperimentResult, *, include_digest: bool
) -> dict[str, object]:
    corpus_run = json.loads(export_formula_research_corpus_run(result.corpus_run))
    analyses = []
    for item, case_run in zip(result.case_analyses, result.corpus_run.case_results, strict=True):
        if (item.case_id, item.case_version) != (case_run.case_id, case_run.case_version):
            raise FormulaResearchValidationError("experiment case analysis order is inconsistent")
        analysis_document = json.loads(export_formula_research_analysis(item.analysis))
        if analysis_document["source"]["replayDigest"] != case_run.result.replay_digest:
            raise FormulaResearchValidationError(
                "experiment analysis does not match case replay digest"
            )
        analyses.append(
            {
                "caseId": item.case_id,
                "caseVersion": item.case_version,
                "analysis": analysis_document,
            }
        )
    document: dict[str, object] = {
        "schemaVersion": result.schema_version,
        "mode": result.mode,
        "experimentId": result.experiment_id,
        "experimentVersion": result.experiment_version,
        "manifestDigest": result.manifest_digest,
        "corpusRun": corpus_run,
        "caseAnalyses": analyses,
    }
    if include_digest:
        document["experimentDigest"] = result.experiment_digest
    return document


def _safe_relative_file(value: object) -> str:
    text = _identity(value, "corpus file")
    if "\\" in text:
        raise FormulaResearchValidationError("corpus file must use POSIX separators")
    path = PurePosixPath(text)
    if (
        path.is_absolute()
        or PureWindowsPath(text).drive
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise FormulaResearchValidationError("corpus file must be a safe relative path")
    if path.suffix.lower() != ".json":
        raise FormulaResearchValidationError("corpus file must be JSON")
    return path.as_posix()


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
        raise FormulaResearchValidationError(f"{label} fields do not match the contract")


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


def _number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise FormulaResearchValidationError(f"{label} must be numeric")
    number = float(value)
    if not math.isfinite(number):
        raise FormulaResearchValidationError(f"{label} must be finite")
    return number


def _json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


__all__ = [
    "EXPERIMENT_REPORT_SCHEMA_VERSION",
    "EXPERIMENT_SCHEMA_VERSION",
    "ExperimentCaseAnalysis",
    "FormulaResearchExperiment",
    "FormulaResearchExperimentResult",
    "export_formula_research_experiment_manifest",
    "export_formula_research_experiment_report",
    "load_formula_research_experiment",
    "run_formula_research_experiment",
]
