from datetime import date

from topicpilot_api.structural_role_audit import AuditRelation, audit_relations

AS_OF = date(2026, 9, 27)


def make_row(
    relation_id: str,
    *,
    role: str | None = "CORE",
    relation_type: str = "PRIMARY",
    valid_from: date = date(2026, 1, 1),
    valid_to: date | None = None,
    approval_state: str | None = "APPROVED",
    superseded_by: str | None = None,
    authority_version: str | None = "v1",
    source_artifact_id: str | None = "artifact:v1",
    source_artifact_hash: str | None = "hash",
    approval_reference: str | None = "approval:v1",
    lineage_hash: str | None = "lineage",
) -> AuditRelation:
    return AuditRelation(
        relation_id=relation_id,
        instrument_id="instrument-1",
        instrument_code="2330",
        instrument_type="EQUITY",
        instrument_active=True,
        instrument_valid_from=None,
        instrument_valid_to=None,
        market_code="TPE",
        market_active=True,
        topic_id="topic-1",
        topic_slug="topic-1",
        topic_status="ACTIVE",
        topic_valid_from=None,
        topic_valid_to=None,
        relation_type=relation_type,
        structural_role=role,
        approval_state=approval_state,
        authority_version=authority_version,
        effective_from=valid_from,
        effective_to=valid_to,
        supersedes_authority_id=None,
        superseded_by_authority_id=superseded_by,
        source_artifact_id=source_artifact_id,
        source_artifact_hash=source_artifact_hash,
        approval_reference=approval_reference,
        correction_sequence=0,
        lineage_hash=lineage_hash,
    )


def test_audit_reports_all_role_drift_categories_without_stopping_at_first() -> None:
    rows = (
        make_row("valid"),
        make_row("null", role=None),
        make_row("empty", role=""),
        make_row("padded", role=" CORE "),
        make_row("lower", role="core"),
        make_row("legacy", role="LEAD"),
        make_row("malformed", role="NOT_A_ROLE"),
        make_row("numeric", role="1"),
    )

    items, summary = audit_relations(rows, AS_OF, {"exists": True, "validated": True})

    assert len(items) == 8
    assert summary.total_rows_scanned == 8
    assert summary.valid_role_rows == 1
    assert summary.invalid_role_rows == 6
    assert summary.null_role_rows == 1
    assert summary.unknown_role_rows == 7
    assert {
        item.invalid_role_category for item in items if item.role_status == "INVALID"
    } == {
        "EMPTY_STRING",
        "WHITESPACE_PADDED",
        "CASE_NORMALIZATION_DRIFT",
        "LEGACY_VOCABULARY_DRIFT",
        "MALFORMED_ENUM_STRING",
        "UNEXPECTED_NUMERIC_OR_STRING",
    }
    assert len(summary.invalid_role_values) == 6
    assert {
        item.root_cause for item in items if item.role_status in {"INVALID", "NULL"}
    } == {"UNKNOWN_ROOT_CAUSE"}


def test_audit_separates_current_historical_future_proposed_and_inactive() -> None:
    rows = [
        make_row("current"),
        make_row("historical", valid_to=date(2026, 1, 31)),
        make_row("future", valid_from=date(2027, 1, 1)),
        make_row("proposed", approval_state="PROPOSED"),
        make_row("inactive", role="RELATED"),
    ]
    rows[-1] = AuditRelation(**{**rows[-1].__dict__, "instrument_active": False})

    items, summary = audit_relations(rows, AS_OF, {"exists": True, "validated": True})

    assert summary.status_counts == {
        "CURRENT_ACTIVE": 1,
        "FUTURE_EFFECTIVE": 1,
        "HISTORICAL_SUPERSEDED": 1,
        "INACTIVE": 1,
        "PROPOSED": 1,
    }
    assert {item.authority_status_bucket for item in items} == {
        "CURRENT_ACTIVE",
        "FUTURE_EFFECTIVE",
        "HISTORICAL_SUPERSEDED",
        "INACTIVE",
        "PROPOSED",
    }


def test_audit_reports_duplicate_current_and_lineage_and_supersession_issues() -> None:
    rows = (
        make_row("duplicate-1"),
        make_row("duplicate-2"),
        make_row("missing-target", superseded_by="missing"),
        make_row("missing-lineage", authority_version="v2", lineage_hash=None),
    )

    _items, summary = audit_relations(rows, AS_OF, {"exists": False, "validated": False})

    assert summary.duplicate_active_authority_rows == 4
    assert summary.supersession_conflict_rows == 1
    assert summary.lineage_inconsistency_rows == 1
    assert summary.database_constraint["exists"] is False
    missing_target = next(
        item for item in _items if item.relation_id == "missing-target"
    )
    assert missing_target.root_cause == "SUPERSESSION_INCONSISTENCY"
