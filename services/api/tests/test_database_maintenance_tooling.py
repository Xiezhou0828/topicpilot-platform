from __future__ import annotations

from datetime import date
from decimal import Decimal

from topicpilot_api.database_maintenance import (
    InstrumentCatalogEntry,
    MaintenanceCatalog,
    RelationCatalogEntry,
    TopicCatalogEntry,
    build_operations,
    validate_maintenance_row,
    validate_maintenance_rows,
)

AS_OF = date(2026, 9, 26)


def _catalog(*, with_instrument: bool = False, with_relations: bool = False) -> MaintenanceCatalog:
    topics = (
        TopicCatalogEntry("topic-1", "ai", "AI", "ACTIVE", date(2026, 1, 1)),
        TopicCatalogEntry("topic-2", "memory", "Memory", "ENABLED", date(2026, 1, 1)),
        TopicCatalogEntry("topic-3", "inactive", "Inactive", "DISABLED", date(2026, 1, 1)),
        TopicCatalogEntry("topic-4", "robotics", "Robotics", "PUBLISHED", date(2026, 1, 1)),
    )
    instrument = InstrumentCatalogEntry(
        "instrument-1", "2330", "TSMC", "TPE", "EQUITY", "TWD", True, date(2026, 1, 1)
    )
    relations = ()
    if with_relations:
        relations = (
            RelationCatalogEntry(
                "relation-1",
                "instrument-1",
                "topic-1",
                "TPE",
                "2330",
                "ai",
                "AI",
                "PRIMARY",
                "v1",
                date(2026, 1, 1),
                None,
                Decimal("1.0"),
                "APPROVED",
            ),
            RelationCatalogEntry(
                "relation-2",
                "instrument-1",
                "topic-2",
                "TPE",
                "2330",
                "memory",
                "Memory",
                "SECONDARY",
                "v1",
                date(2026, 1, 1),
                None,
                Decimal("0.5"),
                "APPROVED",
            ),
        )
    return MaintenanceCatalog(
        markets=frozenset({"TPE", "TWO"}),
        instruments={("TPE", "2330"): instrument} if with_instrument else {},
        topics=topics,
        relations=relations,
    )


def _row(**overrides: str) -> dict[str, str]:
    row = {
        "ACTION": "UPSERT_RELATIONS",
        "STOCK_CODE": "2330",
        "NAME": "TSMC",
        "MARKET": "TPE",
        "INSTRUMENT_TYPE": "EQUITY",
        "CURRENCY": "TWD",
        "ACTIVE/ENABLED": "TRUE",
        "PRIMARY_TOPICS": "ai",
        "PRIMARY_WEIGHTS": "1.0",
        "SECONDARY_TOPICS": "memory",
        "SECONDARY_WEIGHTS": "0.5",
        "AS_OF_DATE": AS_OF.isoformat(),
        "REPRESENTATIVE_TOPIC": "",
        "NOTES": "test",
    }
    row.update(overrides)
    return row


def _errors(row: dict[str, str], catalog: MaintenanceCatalog | None = None) -> set[str]:
    _, errors = validate_maintenance_row(
        row, row_number=2, catalog=catalog or _catalog(), default_as_of=AS_OF
    )
    return {error.error_code for error in errors}


def test_a_zero_relations_is_valid() -> None:
    row = _row(PRIMARY_TOPICS="", PRIMARY_WEIGHTS="", SECONDARY_TOPICS="", SECONDARY_WEIGHTS="")
    item, errors = validate_maintenance_row(
        row, row_number=2, catalog=_catalog(), default_as_of=AS_OF
    )
    assert not errors
    assert item is not None and item.relation_topics() == ()


def test_b_one_primary_is_valid() -> None:
    assert not _errors(_row(SECONDARY_TOPICS="", SECONDARY_WEIGHTS=""))


def test_c_multi_primary_is_valid() -> None:
    assert not _errors(
        _row(
            PRIMARY_TOPICS="ai|memory",
            PRIMARY_WEIGHTS="0.5|2.0",
            SECONDARY_TOPICS="",
            SECONDARY_WEIGHTS="",
        )
    )


def test_d_multi_secondary_is_valid() -> None:
    assert not _errors(
        _row(
            PRIMARY_TOPICS="",
            PRIMARY_WEIGHTS="",
            SECONDARY_TOPICS="ai|memory",
            SECONDARY_WEIGHTS="0.3|0.8",
        )
    )


def test_e_multi_both_is_valid() -> None:
    assert not _errors(
        _row(
            PRIMARY_TOPICS="ai|memory",
            PRIMARY_WEIGHTS="0.5|2.0",
            SECONDARY_TOPICS="robotics",
            SECONDARY_WEIGHTS="0.8",
        )
    )


def test_f_weights_are_independent_and_per_topic() -> None:
    item, errors = validate_maintenance_row(
        _row(
            PRIMARY_TOPICS="ai|memory",
            PRIMARY_WEIGHTS="0.7|1.9",
            SECONDARY_TOPICS="",
            SECONDARY_WEIGHTS="",
        ),
        row_number=2,
        catalog=_catalog(),
        default_as_of=AS_OF,
    )
    assert not errors
    assert item is not None
    assert [weight for _, weight in item.primary_topics] == [Decimal("0.7"), Decimal("1.9")]


def test_g_primary_count_mismatch_rejected() -> None:
    assert "TOPIC_WEIGHT_COUNT_MISMATCH" in _errors(
        _row(PRIMARY_TOPICS="ai|memory", PRIMARY_WEIGHTS="1.0")
    )


def test_h_secondary_count_mismatch_rejected() -> None:
    assert "TOPIC_WEIGHT_COUNT_MISMATCH" in _errors(
        _row(SECONDARY_TOPICS="ai|memory", SECONDARY_WEIGHTS="0.5")
    )


def test_i_primary_range_is_inclusive_and_bounded() -> None:
    assert not _errors(_row(PRIMARY_WEIGHTS="0.5"))
    assert "PRIMARY_WEIGHT_OUT_OF_RANGE" in _errors(_row(PRIMARY_WEIGHTS="2.01"))


def test_j_secondary_range_is_inclusive_and_bounded() -> None:
    assert not _errors(_row(SECONDARY_WEIGHTS="0.3"))
    assert "SECONDARY_WEIGHT_OUT_OF_RANGE" in _errors(_row(SECONDARY_WEIGHTS="0.81"))


def test_k_unknown_topic_rejected() -> None:
    assert "UNKNOWN_TOPIC" in _errors(_row(PRIMARY_TOPICS="unknown"))


def test_l_disabled_topic_rejected() -> None:
    assert "DISABLED_TOPIC" in _errors(_row(PRIMARY_TOPICS="inactive"))


def test_m_duplicate_topic_within_row_rejected() -> None:
    assert "INVALID_TOPIC_LIST" in _errors(_row(PRIMARY_TOPICS="ai|ai", PRIMARY_WEIGHTS="1.0|1.1"))


def test_n_cross_role_duplicate_rejected() -> None:
    assert "PRIMARY_SECONDARY_CONFLICT" in _errors(_row(PRIMARY_TOPICS="ai", SECONDARY_TOPICS="ai"))


def test_o_duplicate_relation_across_rows_rejected() -> None:
    rows = [_row(), _row()]
    _, errors = validate_maintenance_rows(rows, catalog=_catalog(), default_as_of=AS_OF)
    assert any(error.error_code == "DUPLICATE_RELATION" for error in errors)


def test_p_replace_relations_soft_deactivates_unspecified_current_relation() -> None:
    row = _row(
        ACTION="REPLACE_RELATIONS",
        PRIMARY_TOPICS="ai",
        PRIMARY_WEIGHTS="1.0",
        SECONDARY_TOPICS="",
        SECONDARY_WEIGHTS="",
    )
    item, errors = validate_maintenance_row(
        row,
        row_number=2,
        catalog=_catalog(with_instrument=True, with_relations=True),
        default_as_of=AS_OF,
    )
    assert not errors and item is not None
    operations = build_operations(
        (item,), catalog=_catalog(with_instrument=True, with_relations=True)
    )
    assert any(
        operation.operation == "DEACTIVATE" and operation.topic_identifier == "memory"
        for operation in operations
    )


def test_q_add_and_update_master_operations() -> None:
    add, add_errors = validate_maintenance_row(
        _row(
            ACTION="ADD_INSTRUMENT",
            PRIMARY_TOPICS="",
            PRIMARY_WEIGHTS="",
            SECONDARY_TOPICS="",
            SECONDARY_WEIGHTS="",
        ),
        row_number=2,
        catalog=_catalog(),
        default_as_of=AS_OF,
    )
    assert not add_errors and add is not None
    assert build_operations((add,), catalog=_catalog())[0].record_type == "INSTRUMENT"
    update, update_errors = validate_maintenance_row(
        _row(
            ACTION="UPDATE_INSTRUMENT",
            PRIMARY_TOPICS="",
            PRIMARY_WEIGHTS="",
            SECONDARY_TOPICS="",
            SECONDARY_WEIGHTS="",
        ),
        row_number=2,
        catalog=_catalog(with_instrument=True),
        default_as_of=AS_OF,
    )
    assert not update_errors and update is not None
    assert (
        build_operations((update,), catalog=_catalog(with_instrument=True))[0].operation
        == "UPDATE_INSTRUMENT"
    )


def test_r_representative_topic_is_explicit_only() -> None:
    item, errors = validate_maintenance_row(
        _row(
            REPRESENTATIVE_TOPIC="ai",
            PRIMARY_TOPICS="",
            PRIMARY_WEIGHTS="",
            SECONDARY_TOPICS="",
            SECONDARY_WEIGHTS="",
        ),
        row_number=2,
        catalog=_catalog(),
        default_as_of=AS_OF,
    )
    assert not errors and item is not None
    assert item.representative_topic is not None
    zero_item, zero_errors = validate_maintenance_row(
        _row(PRIMARY_TOPICS="", PRIMARY_WEIGHTS="", SECONDARY_TOPICS="", SECONDARY_WEIGHTS=""),
        row_number=2,
        catalog=_catalog(),
        default_as_of=AS_OF,
    )
    assert not zero_errors and zero_item is not None and zero_item.representative_topic is None
