import json
from dataclasses import replace
from datetime import date

import pytest

from topicpilot_api.topic_engine import (
    EvaluationBundle,
    FeatureRuntimeConfig,
    FormulaResearchValidationError,
    ResearchBounds,
    ResearchCandidate,
    ScoringPolicy,
    TopicScorer,
    aggregate_features,
    analyze_formula_research,
    export_formula_research_analysis,
    run_formula_research,
)
from topicpilot_api.topic_engine.features.availability import availability_features
from topicpilot_api.topic_engine.features.hierarchy import hierarchy_features
from topicpilot_api.topic_engine.features.membership import membership_features

pytestmark = pytest.mark.research


class SyntheticBreadthPassthrough:
    """Test-only behavior; not a TopicPilot formula candidate."""

    def aggregate(self, components, _policy):
        return components["breadth"]


def aggregates():
    topic_ids = ("d", "b", "a", "c")
    bundle = EvaluationBundle(
        "calc-v1",
        date(2026, 8, 8),
        topics=tuple({"id": topic_id} for topic_id in topic_ids),
        memberships=tuple(
            {"topic_id": topic_id, "instrument_id": f"i-{topic_id}"} for topic_id in topic_ids
        ),
        observations=tuple(
            {"topic_id": topic_id, "instrument_id": f"i-{topic_id}"} for topic_id in topic_ids
        ),
    )
    config = FeatureRuntimeConfig(
        "features-v1",
        "feature-runtime-v1",
        "aggregate-v1",
        ("membership_count",),
        (membership_features, hierarchy_features, availability_features),
    )
    result = aggregate_features(bundle, config)
    return replace(
        result,
        aggregates=tuple(replace(item, status="READY_UNSCORED") for item in result.aggregates),
    )


def candidate(candidate_id, scores):
    scorer = TopicScorer(
        f"scorer-{candidate_id}",
        component_collector=lambda aggregate: {
            "breadth": scores[aggregate.topic_id],
            "leadership": 0.0,
        },
        aggregation_policy=SyntheticBreadthPassthrough(),
    )
    return ResearchCandidate(
        candidate_id,
        "v1",
        scorer,
        ScoringPolicy(candidate_id, "v1", (("fixture", "synthetic"),)),
        ResearchBounds(0.0, 100.0),
        ResearchBounds(0.0, 100.0),
    )


def research_result():
    left = candidate("candidate-a", {"a": 0.0, "b": 10.0, "c": None, "d": None})
    right = candidate("candidate-b", {"a": 0.0, "b": None, "c": 30.0, "d": None})
    return run_formula_research(aggregates(), (right, left), research_runtime_version="research-v1")


def test_analysis_is_descriptive_null_safe_and_deterministic():
    analysis = analyze_formula_research(research_result(), analysis_runtime_version="analysis-v1")
    repeated = analyze_formula_research(research_result(), analysis_runtime_version="analysis-v1")

    assert analysis == repeated
    assert analysis.mode == "RESEARCH_ONLY"
    assert [item.candidate_id for item in analysis.candidate_distributions] == [
        "candidate-a",
        "candidate-b",
    ]
    left = analysis.candidate_distributions[0]
    assert (left.topic_count, left.scored_count, left.null_count, left.zero_count) == (
        4,
        2,
        2,
        1,
    )
    assert (left.minimum, left.maximum, left.mean, left.median) == (0.0, 10.0, 5.0, 5.0)

    pair = analysis.pairwise_comparisons[0]
    assert (
        pair.both_scored_count,
        pair.left_only_count,
        pair.right_only_count,
        pair.both_null_count,
    ) == (1, 1, 1, 1)
    assert pair.mean_absolute_difference == 0.0
    assert pair.maximum_absolute_difference == 0.0
    assert pair.topic_differences[0].topic_id == "a"


def test_export_is_deterministic_json_safe_and_lineage_complete():
    source = research_result()
    analysis = analyze_formula_research(source, analysis_runtime_version="analysis-v1")
    exported = export_formula_research_analysis(analysis)
    repeated = export_formula_research_analysis(analysis)
    document = json.loads(exported)

    assert exported == repeated
    assert document["mode"] == "RESEARCH_ONLY"
    assert document["schemaVersion"] == "topic-formula-research-analysis.v1"
    assert document["source"]["replayDigest"] == source.replay_digest
    assert document["analysisDigest"] == analysis.analysis_digest
    assert document["candidateDistributions"][0]["policyConfiguration"] == [
        ["fixture", "synthetic"]
    ]
    assert document["candidateDistributions"][0]["scorerRuntimeVersion"] == "scorer-candidate-a"
    assert "callable" not in exported.lower()
    assert "persistence" not in exported.lower()


def test_analysis_rejects_non_research_or_inconsistent_source():
    source = research_result()
    with pytest.raises(FormulaResearchValidationError, match="RESEARCH_ONLY"):
        analyze_formula_research(
            replace(source, mode="PRODUCTION"), analysis_runtime_version="analysis-v1"
        )

    topic = source.topic_comparisons[0]
    output = topic.candidates[0]
    changed_topic = replace(
        topic,
        candidates=(replace(output, score=99.0), *topic.candidates[1:]),
    )
    with pytest.raises(FormulaResearchValidationError, match="does not match"):
        analyze_formula_research(
            replace(source, topic_comparisons=(changed_topic, *source.topic_comparisons[1:])),
            analysis_runtime_version="analysis-v1",
        )


def test_export_rejects_tampered_analysis_digest():
    analysis = analyze_formula_research(research_result(), analysis_runtime_version="analysis-v1")
    with pytest.raises(FormulaResearchValidationError, match="digest"):
        export_formula_research_analysis(replace(analysis, analysis_digest="0" * 64))
