import copy
import json
from pathlib import Path

import pytest

from topicpilot_api.topic_engine import (
    FormulaResearchValidationError,
    build_historical_formula_research_corpus,
    build_participation_research_candidate,
    export_formula_research_corpus,
    export_historical_evidence_dataset,
    load_formula_research_experiment,
    load_historical_evidence_dataset,
    parse_historical_evidence_dataset,
    run_formula_research_corpus,
)

pytestmark = pytest.mark.research

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "fixtures" / "research"
FIXTURE = FIXTURE_DIR / "topic_formula_historical_evidence.v1.json"
EXPERIMENT = FIXTURE_DIR / "topic_formula_experiment.v1.json"


def _document():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_historical_fixture_round_trips_and_order_is_not_identity():
    original = load_historical_evidence_dataset(FIXTURE)
    reordered = _document()
    reordered["sourceReferences"].reverse()
    reordered["cases"].reverse()
    for case in reordered["cases"]:
        case["labels"].reverse()
        case["topics"].reverse()
        for topic in case["topics"]:
            topic["coreMembers"].reverse()
            topic["leaderInstrumentIds"].reverse()

    repeated = parse_historical_evidence_dataset(reordered)

    assert original == repeated
    assert len(original.content_digest) == 64
    assert json.loads(export_historical_evidence_dataset(original)) == _document()


def test_bridge_builds_explicit_counts_and_preserves_missing_coverage():
    dataset = load_historical_evidence_dataset(FIXTURE)
    corpus = build_historical_formula_research_corpus(dataset)

    assert [case.case_id for case in corpus.cases] == [
        "explicit-core-and-leaders",
        "missing-leader-set",
    ]
    alpha = corpus.cases[0].aggregates.aggregates[0]
    alpha_features = {feature.feature_name: feature for feature in alpha.feature_results}
    breadth = alpha_features["synthetic_breadth_participation_counts"]
    leadership = alpha_features["synthetic_leadership_participation_counts"]
    assert breadth.value == {
        "positiveCount": 1,
        "unchangedCount": 1,
        "negativeCount": 1,
    }
    assert breadth.coverage == 0.75
    assert breadth.quality_flags == ("MISSING_MEMBER_EVIDENCE",)
    assert leadership.value == {
        "positiveCount": 1,
        "unchangedCount": 0,
        "negativeCount": 1,
    }
    assert leadership.coverage == 1.0

    beta = corpus.cases[1].aggregates.aggregates[0]
    beta_features = {feature.feature_name: feature for feature in beta.feature_results}
    assert beta.status == "DATA_INSUFFICIENT"
    assert beta_features["synthetic_breadth_participation_counts"].value == {
        "positiveCount": 1,
        "unchangedCount": 0,
        "negativeCount": 0,
    }
    assert beta_features["synthetic_breadth_participation_counts"].coverage == 0.5
    assert beta_features["synthetic_leadership_participation_counts"].value is None
    assert beta_features["synthetic_leadership_participation_counts"].coverage is None
    assert beta_features["synthetic_leadership_participation_counts"].quality_flags == (
        "NO_EXPLICIT_LEADER_SET",
    )


def test_generated_corpus_is_deterministic_and_runs_existing_candidates():
    dataset = load_historical_evidence_dataset(FIXTURE)
    first = build_historical_formula_research_corpus(dataset)
    repeated = build_historical_formula_research_corpus(dataset)
    experiment = load_formula_research_experiment(EXPERIMENT)
    candidates = tuple(
        build_participation_research_candidate(spec) for spec in experiment.candidate_specs
    )

    assert first == repeated
    assert export_formula_research_corpus(first) == export_formula_research_corpus(repeated)
    run = run_formula_research_corpus(
        first,
        candidates,
        research_runtime_version="historical-evidence-research.v1",
    )
    assert [item.case_id for item in run.case_results] == [
        "explicit-core-and-leaders",
        "missing-leader-set",
    ]
    alpha_outputs = run.case_results[0].result.topic_comparisons[0].candidates
    assert all(output.score is not None for output in alpha_outputs)
    beta_outputs = run.case_results[1].result.topic_comparisons[0].candidates
    assert all(output.score is None for output in beta_outputs)
    lowered = export_formula_research_corpus(first).lower()
    for forbidden in ("threshold", "futurereturn", "ranking", "winner", "productiondefault"):
        assert forbidden not in lowered


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda document: document["cases"][0]["topics"][0]["coreMembers"][0].update(
                observationDate="2026-08-06"
            ),
            "after case asOf",
        ),
        (
            lambda document: document["cases"][0]["topics"][0]["coreMembers"][0].update(
                membershipValidFrom="2026-08-06"
            ),
            "does not contain case asOf",
        ),
        (
            lambda document: document["cases"][0]["topics"][0].update(
                leaderInstrumentIds=["UNKNOWN"]
            ),
            "explicit CORE members",
        ),
        (
            lambda document: document["cases"][0]["topics"][0]["coreMembers"][3].update(
                observationDate="2026-08-05"
            ),
            "MISSING evidence",
        ),
        (
            lambda document: document["cases"][0]["topics"][0]["coreMembers"][0].update(
                participationState="STRONG"
            ),
            "unsupported participationState",
        ),
    ],
)
def test_point_in_time_and_explicit_population_rules_fail_closed(mutate, message):
    document = _document()
    mutate(document)
    with pytest.raises(FormulaResearchValidationError, match=message):
        parse_historical_evidence_dataset(document)


def test_tampering_duplicates_and_unknown_fields_fail_closed():
    tampered = _document()
    tampered["cases"][0]["topics"][0]["coreMembers"][0]["participationState"] = "NEGATIVE"
    with pytest.raises(FormulaResearchValidationError, match="digest"):
        parse_historical_evidence_dataset(tampered)

    duplicate = _document()
    duplicate["cases"][0]["topics"][0]["coreMembers"].append(
        copy.deepcopy(duplicate["cases"][0]["topics"][0]["coreMembers"][0])
    )
    with pytest.raises(FormulaResearchValidationError, match="unique"):
        parse_historical_evidence_dataset(duplicate)

    unknown = _document()
    unknown["classificationThreshold"] = 0.01
    with pytest.raises(FormulaResearchValidationError, match="fields"):
        parse_historical_evidence_dataset(unknown)
