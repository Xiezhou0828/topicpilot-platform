import copy
import json
from dataclasses import replace
from pathlib import Path

import pytest

from topicpilot_api.topic_engine import (
    FormulaResearchValidationError,
    ResearchBounds,
    ResearchCandidate,
    ScoringPolicy,
    TopicScorer,
    export_formula_research_corpus,
    export_formula_research_corpus_run,
    load_formula_research_corpus,
    parse_formula_research_corpus,
    run_formula_research_corpus,
)

pytestmark = pytest.mark.research

FIXTURE = (
    Path(__file__).resolve().parents[3]
    / "fixtures"
    / "research"
    / "topic_formula_replay_corpus.v1.json"
)


class TestOnlyMeanAggregation:
    """Synthetic test behavior; this is not a TopicPilot formula candidate."""

    def aggregate(self, components, _policy):
        values = tuple(value for value in components.values() if value is not None)
        return sum(values) / len(values) if values else None


class TestOnlyMaximumAggregation:
    """Synthetic test behavior; this is not a TopicPilot formula candidate."""

    def aggregate(self, components, _policy):
        values = tuple(value for value in components.values() if value is not None)
        return max(values) if values else None


def _components(aggregate):
    evidence = {feature.feature_name: feature.value for feature in aggregate.feature_results}
    return {
        "breadth": evidence["synthetic_breadth_input"],
        "leadership": evidence["synthetic_leadership_input"],
    }


def _candidate(candidate_id, aggregation):
    return ResearchCandidate(
        candidate_id,
        "v1",
        TopicScorer(
            f"test-scorer-{candidate_id}",
            component_collector=_components,
            aggregation_policy=aggregation,
        ),
        ScoringPolicy(candidate_id, "v1", (("fixture", "synthetic"),)),
        ResearchBounds(0.0, 100.0),
        ResearchBounds(0.0, 100.0),
    )


def _document():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_public_fixture_loads_canonically_and_preserves_null_and_zero():
    corpus = load_formula_research_corpus(FIXTURE)

    assert corpus.mode == "RESEARCH_ONLY"
    assert len(corpus.content_digest) == 64
    assert [case.case_id for case in corpus.cases] == [
        "complete-neutral",
        "invalid-evidence",
        "missing-evidence",
        "valid-zero",
    ]
    zero_features = corpus.cases[-1].aggregates.aggregates[0].feature_results
    assert [feature.value for feature in zero_features] == [0.0, 0.0]
    missing_features = corpus.cases[2].aggregates.aggregates[0].feature_results
    assert missing_features[0].value is None
    assert json.loads(export_formula_research_corpus(corpus)) == _document()


def test_fixture_order_does_not_change_canonical_identity():
    document = _document()
    reordered = copy.deepcopy(document)
    reordered["cases"].reverse()
    for case in reordered["cases"]:
        case["labels"].reverse()
        case["aggregation"]["topics"].reverse()
        for topic in case["aggregation"]["topics"]:
            topic["features"].reverse()

    assert parse_formula_research_corpus(reordered) == parse_formula_research_corpus(document)


def test_tampering_duplicate_identity_and_bad_quality_fail_closed():
    tampered = _document()
    tampered["cases"][0]["aggregation"]["topics"][0]["features"][0]["value"] = 61.0
    with pytest.raises(FormulaResearchValidationError, match="digest"):
        parse_formula_research_corpus(tampered)

    duplicate = _document()
    duplicate["cases"].append(copy.deepcopy(duplicate["cases"][0]))
    with pytest.raises(FormulaResearchValidationError, match="unique"):
        parse_formula_research_corpus(duplicate)

    bad_quality = _document()
    bad_quality["cases"][0]["aggregation"]["topics"][0]["quality"]["readyFeatureCount"] = 1
    with pytest.raises(FormulaResearchValidationError, match="quality feature counts"):
        parse_formula_research_corpus(bad_quality)


def test_non_finite_or_private_shaped_fixture_content_fails_closed():
    non_finite = _document()
    non_finite["cases"][0]["aggregation"]["topics"][0]["features"][0]["value"] = float("nan")
    with pytest.raises(FormulaResearchValidationError, match="non-finite"):
        parse_formula_research_corpus(non_finite)

    private_shape = _document()
    private_shape["cases"][0]["aggregation"]["topics"][0]["features"][0]["metadata"]["apiToken"] = (
        "not-a-real-token"
    )
    with pytest.raises(FormulaResearchValidationError, match="forbidden public key"):
        parse_formula_research_corpus(private_shape)


def test_cross_case_run_is_candidate_order_independent_and_replayable():
    corpus = load_formula_research_corpus(FIXTURE)
    mean = _candidate("candidate-mean-test-only", TestOnlyMeanAggregation())
    maximum = _candidate("candidate-max-test-only", TestOnlyMaximumAggregation())

    first = run_formula_research_corpus(
        corpus,
        (mean, maximum),
        research_runtime_version="corpus-research-v1",
    )
    repeated = run_formula_research_corpus(
        corpus,
        (maximum, mean),
        research_runtime_version="corpus-research-v1",
    )

    assert first == repeated
    assert len(first.run_digest) == 64
    assert first.candidate_identities == (
        ("candidate-max-test-only", "v1"),
        ("candidate-mean-test-only", "v1"),
    )
    assert [item.case_id for item in first.case_results] == [
        "complete-neutral",
        "invalid-evidence",
        "missing-evidence",
        "valid-zero",
    ]
    assert all(len(item.result.replay_digest) == 64 for item in first.case_results)

    zero_case = first.case_results[-1]
    assert all(output.score == 0.0 for output in zero_case.result.topic_comparisons[0].candidates)
    assert all(
        item.result.topic_comparisons[0].candidates[0].eligibility == "INELIGIBLE"
        for item in first.case_results[1:3]
    )

    exported = export_formula_research_corpus_run(first)
    document = json.loads(exported)
    assert document["corpusContentDigest"] == corpus.content_digest
    assert document["runDigest"] == first.run_digest
    assert "callable" not in exported.lower()
    assert "persistence" not in exported.lower()


def test_corpus_and_run_digest_tampering_is_rejected():
    corpus = load_formula_research_corpus(FIXTURE)
    candidate = _candidate("candidate-test-only", TestOnlyMeanAggregation())
    run = run_formula_research_corpus(
        corpus,
        (candidate,),
        research_runtime_version="corpus-research-v1",
    )

    with pytest.raises(FormulaResearchValidationError, match="corpus digest"):
        run_formula_research_corpus(
            replace(corpus, content_digest="0" * 64),
            (candidate,),
            research_runtime_version="corpus-research-v1",
        )
    with pytest.raises(FormulaResearchValidationError, match="run digest"):
        export_formula_research_corpus_run(replace(run, run_digest="0" * 64))
