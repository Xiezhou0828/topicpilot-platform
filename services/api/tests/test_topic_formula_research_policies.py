from dataclasses import replace
from pathlib import Path

import pytest

from topicpilot_api.topic_engine import (
    DIFFUSION_PARTICIPATION,
    STRICT_PARTICIPATION,
    FormulaResearchValidationError,
    ParticipationResearchSpec,
    WeightedArithmeticResearchAggregation,
    analyze_formula_research,
    build_participation_research_candidate,
    load_formula_research_corpus,
    run_formula_research,
    run_formula_research_corpus,
)

FIXTURE = (
    Path(__file__).resolve().parents[3]
    / "fixtures"
    / "research"
    / "topic_formula_candidate_evidence.v1.json"
)
SOURCES = (
    "conference-board-diffusion-index",
    "federal-reserve-g17-diffusion-index",
    "oecd-jrc-composite-indicator-handbook",
)


def _spec(candidate_id, method, *, breadth_weight=0.5, leadership_weight=0.5):
    return ParticipationResearchSpec(
        candidate_id,
        "v1",
        f"research-scorer-{candidate_id}.v1",
        "synthetic_breadth_participation_counts",
        "v1",
        method,
        breadth_weight,
        "synthetic_leadership_participation_counts",
        "v1",
        method,
        leadership_weight,
        SOURCES,
    )


def _candidate(candidate_id, method, **weights):
    return build_participation_research_candidate(_spec(candidate_id, method, **weights))


def _case(run, case_id):
    return next(item.result for item in run.case_results if item.case_id == case_id)


def _topic(result, topic_id):
    return next(item for item in result.topic_comparisons if item.topic_id == topic_id)


def test_strict_and_diffusion_candidate_mechanics_are_explicit_and_distinct():
    corpus = load_formula_research_corpus(FIXTURE)
    strict = _candidate("strict-participation-baseline", STRICT_PARTICIPATION)
    diffusion = _candidate("diffusion-participation-baseline", DIFFUSION_PARTICIPATION)

    run = run_formula_research_corpus(
        corpus,
        (strict, diffusion),
        research_runtime_version="candidate-research-v1",
    )
    complete = _topic(_case(run, "complete-mixed-counts"), "synthetic-topic-alpha")
    by_candidate = {item.candidate_id: item for item in complete.candidates}

    strict_output = by_candidate["strict-participation-baseline"]
    assert dict(strict_output.components)["breadth"] == pytest.approx(60.0)
    assert dict(strict_output.components)["leadership"] == pytest.approx(100.0 / 3.0)
    assert strict_output.score == pytest.approx((60.0 + 100.0 / 3.0) / 2.0)

    diffusion_output = by_candidate["diffusion-participation-baseline"]
    assert dict(diffusion_output.components) == {"breadth": 70.0, "leadership": 50.0}
    assert diffusion_output.score == pytest.approx(60.0)
    assert diffusion_output.grade is None
    assert diffusion_output.confidence is None


def test_neutral_half_credit_valid_zero_and_missing_remain_distinct():
    corpus = load_formula_research_corpus(FIXTURE)
    strict = _candidate("strict-participation-baseline", STRICT_PARTICIPATION)
    diffusion = _candidate("diffusion-participation-baseline", DIFFUSION_PARTICIPATION)
    run = run_formula_research_corpus(
        corpus,
        (diffusion, strict),
        research_runtime_version="candidate-research-v1",
    )

    unchanged = _topic(_case(run, "unchanged-sensitive"), "synthetic-topic-alpha")
    unchanged_by_candidate = {item.candidate_id: item for item in unchanged.candidates}
    assert unchanged_by_candidate["strict-participation-baseline"].score == 0.0
    assert unchanged_by_candidate["diffusion-participation-baseline"].score == 50.0

    zero = _topic(_case(run, "valid-zero-participation"), "synthetic-topic-alpha")
    assert all(output.score == 0.0 for output in zero.candidates)
    assert all(output.eligibility == "ELIGIBLE" for output in zero.candidates)

    missing = _topic(_case(run, "missing-counts"), "synthetic-topic-alpha")
    assert all(output.score is None for output in missing.candidates)
    assert all(output.eligibility == "INELIGIBLE" for output in missing.candidates)
    assert all(output.components == () for output in missing.candidates)


def test_candidate_order_is_irrelevant_and_analysis_preserves_policy_lineage():
    corpus = load_formula_research_corpus(FIXTURE)
    strict = _candidate("strict-participation-baseline", STRICT_PARTICIPATION)
    diffusion = _candidate("diffusion-participation-baseline", DIFFUSION_PARTICIPATION)

    first = run_formula_research_corpus(
        corpus,
        (strict, diffusion),
        research_runtime_version="candidate-research-v1",
    )
    repeated = run_formula_research_corpus(
        corpus,
        (diffusion, strict),
        research_runtime_version="candidate-research-v1",
    )
    assert first == repeated

    analysis = analyze_formula_research(
        _case(first, "complete-mixed-counts"),
        analysis_runtime_version="candidate-analysis-v1",
    )
    assert len(analysis.candidate_distributions) == 2
    assert len(analysis.pairwise_comparisons) == 1
    configuration = dict(analysis.candidate_distributions[0].policy_configuration)
    assert configuration["mode"] == "RESEARCH_ONLY"
    assert configuration["aggregation_method"] == "WEIGHTED_ARITHMETIC"
    assert configuration["source_references"] == ",".join(SOURCES)


@pytest.mark.parametrize(
    "change",
    [
        {"breadth_method": "UNKNOWN"},
        {"breadth_weight": 0.0, "leadership_weight": 1.0},
        {"breadth_weight": 0.6, "leadership_weight": 0.5},
        {"breadth_weight": float("nan")},
        {"source_references": ()},
        {"source_references": tuple(reversed(SOURCES))},
        {"source_references": (SOURCES[0], SOURCES[0])},
    ],
)
def test_candidate_spec_rejects_implicit_or_invalid_policy_choices(change):
    values = _spec("candidate", STRICT_PARTICIPATION).__dict__ | change
    with pytest.raises(FormulaResearchValidationError):
        ParticipationResearchSpec(**values)


@pytest.mark.parametrize(
    "bad_value",
    [
        {"positiveCount": True, "unchangedCount": 0, "negativeCount": 1},
        {"positiveCount": -1, "unchangedCount": 0, "negativeCount": 1},
        {"positiveCount": 1.5, "unchangedCount": 0, "negativeCount": 1},
        {"positiveCount": 1, "negativeCount": 1},
        {"positiveCount": 1, "unchangedCount": 0, "negativeCount": 1, "extra": 0},
    ],
)
def test_malformed_participation_counts_fail_closed(bad_value):
    corpus = load_formula_research_corpus(FIXTURE)
    source = corpus.cases[0].aggregates
    topic = source.aggregates[0]
    bad_feature = replace(topic.feature_results[0], value=bad_value)
    bad_topic = replace(topic, feature_results=(bad_feature, *topic.feature_results[1:]))
    aggregates = replace(source, aggregates=(bad_topic, *source.aggregates[1:]))
    candidate = _candidate("strict-participation-baseline", STRICT_PARTICIPATION)

    with pytest.raises(FormulaResearchValidationError):
        run_formula_research(
            aggregates,
            (candidate,),
            research_runtime_version="candidate-research-v1",
        )


def test_zero_denominator_is_null_not_zero_and_component_boundary_fails_closed():
    corpus = load_formula_research_corpus(FIXTURE)
    source = corpus.cases[0].aggregates
    topic = source.aggregates[0]
    zero_total = {"positiveCount": 0, "unchangedCount": 0, "negativeCount": 0}
    features = tuple(replace(feature, value=zero_total) for feature in topic.feature_results)
    aggregates = replace(source, aggregates=(replace(topic, feature_results=features),))
    candidate = _candidate("strict-participation-baseline", STRICT_PARTICIPATION)

    result = run_formula_research(
        aggregates,
        (candidate,),
        research_runtime_version="candidate-research-v1",
    )
    output = result.topic_comparisons[0].candidates[0]
    assert output.score is None
    assert output.status == "DEFERRED"
    assert output.eligibility == "ELIGIBLE"
    assert dict(output.components) == {"breadth": None, "leadership": None}

    aggregation = WeightedArithmeticResearchAggregation(0.5, 0.5)
    with pytest.raises(FormulaResearchValidationError, match="breadth and leadership"):
        aggregation.aggregate({"breadth": 50.0}, candidate.policy)
