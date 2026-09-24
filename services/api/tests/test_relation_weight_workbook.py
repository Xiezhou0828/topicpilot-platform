from decimal import Decimal

import pytest

from topicpilot_api.relation_weight_authority import (
    RelationIdentity,
    RelationWeightIdentityError,
    generate_proposals,
)
from topicpilot_api.relation_weight_workbook import (
    WorkbookWeightValidationError,
    export_proposal_rows,
    validate_workbook_row,
)

UNIVERSE = (
    RelationIdentity("TPE", "2301", "topic-a", "PRIMARY"),
    RelationIdentity("TPE", "2301", "topic-d", "PRIMARY"),
    RelationIdentity("TPE", "2301", "topic-b", "SECONDARY"),
    RelationIdentity("TPE", "2301", "topic-c", "SECONDARY"),
)


def test_workbook_secondary_topics_and_weights_are_strict_positional_pairs():
    row = validate_workbook_row(
        {
            "market": "TPE",
            "symbol": "2301",
            "primary_topics": "topic-a",
            "primary_weights": "1.0",
            "secondary_topics": "topic-b|topic-c",
            "secondary_weights": "0.5|0.8",
        },
        relation_universe=UNIVERSE,
    )
    assert row.primary_topics == ("topic-a",)
    assert row.primary_weights == (Decimal("1.0"),)
    assert row.secondary_topics == ("topic-b", "topic-c")
    assert row.secondary_weights == (Decimal("0.5"), Decimal("0.8"))


def test_workbook_count_mismatch_fails():
    with pytest.raises(WorkbookWeightValidationError, match="count must match"):
        validate_workbook_row(
            {
                "market": "TPE",
                "symbol": "2301",
                "primary_topics": "topic-a",
                "primary_weights": "1.0",
                "secondary_topics": "topic-b|topic-c",
                "secondary_weights": "0.5",
            },
            relation_universe=UNIVERSE,
        )


def test_workbook_duplicate_and_unknown_relations_fail():
    with pytest.raises(WorkbookWeightValidationError, match="duplicate"):
        validate_workbook_row(
            {
                "market": "TPE",
                "symbol": "2301",
                "primary_topics": "topic-a",
                "primary_weights": "1.0",
                "secondary_topics": "topic-b|topic-b",
                "secondary_weights": "0.5|0.5",
            },
            relation_universe=UNIVERSE,
        )

    with pytest.raises(RelationWeightIdentityError, match="unknown stock/Topic"):
        validate_workbook_row(
            {
                "market": "TPE",
                "symbol": "9999",
                "primary_topics": "topic-a",
                "primary_weights": "1.0",
                "secondary_topics": "",
                "secondary_weights": "",
            },
            relation_universe=UNIVERSE,
        )


def test_workbook_export_keeps_owner_editable_values():
    current = [
        {"market": "TPE", "symbol": "2301", "topic": "topic-a", "relation_type": "PRIMARY"},
        {"market": "TPE", "symbol": "2301", "topic": "topic-b", "relation_type": "SECONDARY"},
        {"market": "TPE", "symbol": "2301", "topic": "topic-c", "relation_type": "SECONDARY"},
    ]
    evidence = [
        {**row, "recovery_status": "NO_HISTORICAL_WEIGHT"} for row in current
    ]
    result = generate_proposals(current, evidence)
    rows = export_proposal_rows(result.proposals)
    assert rows == (
        {
            "symbol": "2301",
            "name": "",
            "market": "TPE",
            "representative_topic": "",
            "primary_topics": "topic-a",
            "secondary_topics": "topic-b|topic-c",
            "primary_weights": "1.0",
            "secondary_weights": "0.5|0.5",
            "effective_date": "2026-09-24",
            "reason": "",
            "evidence_note": "",
        },
    )


def test_workbook_allows_multiple_primary_and_zero_relations_without_inference():
    multi = validate_workbook_row(
        {
            "market": "TPE",
            "symbol": "2301",
            "representative_topic": "display-only-topic",
            "primary_topics": "topic-a|topic-d",
            "primary_weights": "1.0|1.5",
            "secondary_topics": "",
            "secondary_weights": "",
        },
        relation_universe=UNIVERSE,
    )
    assert multi.primary_topics == ("topic-a", "topic-d")
    assert multi.representative_topic == "display-only-topic"

    empty = validate_workbook_row(
        {
            "market": "TPE",
            "symbol": "9999",
            "primary_topics": "",
            "primary_weights": "",
            "secondary_topics": "",
            "secondary_weights": "",
        },
        relation_universe=UNIVERSE,
    )
    assert empty.identities() == ()


def test_workbook_rejects_cross_role_duplicate_topic():
    with pytest.raises(WorkbookWeightValidationError, match="both PRIMARY and SECONDARY"):
        validate_workbook_row(
            {
                "market": "TPE",
                "symbol": "2301",
                "primary_topics": "topic-a",
                "primary_weights": "1.0",
                "secondary_topics": "topic-a",
                "secondary_weights": "0.5",
            },
            relation_universe=UNIVERSE,
        )
