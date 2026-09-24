import pytest

from topicpilot_api.relation_weight_authority import (
    RelationIdentity,
    RelationWeightRangeError,
)
from topicpilot_api.relation_weight_workbook import (
    WorkbookWeightValidationError,
    validate_workbook_row,
)


LEGACY_MULTI_PRIMARY_UNIVERSE = (
    RelationIdentity("TPE", "2408", "DRAM／DDR", "PRIMARY"),
    RelationIdentity("TPE", "2408", "記憶體模組／通路", "PRIMARY"),
    RelationIdentity("TPE", "2408", "記憶體製程", "SECONDARY"),
)


def test_case_a_multi_primary_preserves_legacy_relations_without_representative_inference():
    row = validate_workbook_row(
        {
            "symbol": "2408",
            "name": "南亞科",
            "market": "TPE",
            "primary_topics": "DRAM／DDR|記憶體模組／通路",
            "primary_weights": "1.4|1.4",
            "secondary_topics": "",
            "secondary_weights": "",
        },
        relation_universe=LEGACY_MULTI_PRIMARY_UNIVERSE,
    )
    assert row.primary_topics == ("DRAM／DDR", "記憶體模組／通路")
    assert row.primary_weights[0] == row.primary_weights[1]
    assert row.representative_topic is None


def test_case_b_zero_primary_is_valid_with_secondary_or_empty_relations():
    secondary_only = validate_workbook_row(
        {
            "symbol": "2408",
            "market": "TPE",
            "primary_topics": "",
            "primary_weights": "",
            "secondary_topics": "記憶體製程",
            "secondary_weights": "0.5",
        },
        relation_universe=LEGACY_MULTI_PRIMARY_UNIVERSE,
    )
    empty = validate_workbook_row(
        {
            "symbol": "9999",
            "market": "TPE",
            "primary_topics": "",
            "primary_weights": "",
            "secondary_topics": "",
            "secondary_weights": "",
        },
        relation_universe=LEGACY_MULTI_PRIMARY_UNIVERSE,
    )
    assert secondary_only.primary_topics == ()
    assert secondary_only.secondary_topics == ("記憶體製程",)
    assert empty.identities() == ()


def test_case_c_multi_secondary_uses_positional_pipe_mapping():
    universe = tuple(
        RelationIdentity("TPE", "2408", topic, "SECONDARY")
        for topic in ("A", "B", "C")
    )
    row = validate_workbook_row(
        {
            "symbol": "2408",
            "market": "TPE",
            "primary_topics": "",
            "primary_weights": "",
            "secondary_topics": "A|B|C",
            "secondary_weights": "0.4|0.5|0.8",
        },
        relation_universe=universe,
    )
    assert row.secondary_topics == ("A", "B", "C")
    assert tuple(str(weight) for weight in row.secondary_weights) == ("0.4", "0.5", "0.8")


def test_case_d_representative_topic_is_reserved_and_not_first_primary():
    row = validate_workbook_row(
        {
            "symbol": "2408",
            "market": "TPE",
            "representative_topic": "owner-display-candidate",
            "primary_topics": "DRAM／DDR|記憶體模組／通路",
            "primary_weights": "1.4|1.4",
            "secondary_topics": "",
            "secondary_weights": "",
        },
        relation_universe=LEGACY_MULTI_PRIMARY_UNIVERSE,
    )
    assert row.representative_topic == "owner-display-candidate"
    assert row.representative_topic != row.primary_topics[0]


def test_case_e_invalid_positional_count_fails():
    with pytest.raises(WorkbookWeightValidationError, match="count must match"):
        validate_workbook_row(
            {
                "symbol": "2408",
                "market": "TPE",
                "primary_topics": "DRAM／DDR|記憶體模組／通路",
                "primary_weights": "1.4",
                "secondary_topics": "",
                "secondary_weights": "",
            },
            relation_universe=LEGACY_MULTI_PRIMARY_UNIVERSE,
        )


def test_case_f_out_of_range_weight_fails():
    with pytest.raises(RelationWeightRangeError, match="outside inclusive range"):
        validate_workbook_row(
            {
                "symbol": "2408",
                "market": "TPE",
                "primary_topics": "DRAM／DDR",
                "primary_weights": "2.1",
                "secondary_topics": "",
                "secondary_weights": "",
            },
            relation_universe=LEGACY_MULTI_PRIMARY_UNIVERSE,
        )
