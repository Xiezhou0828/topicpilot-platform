from __future__ import annotations

import copy
import json
from dataclasses import replace
from datetime import date
from pathlib import Path

import pytest

from topicpilot_api.normalizer.contracts import stable_hash
from topicpilot_api.reference_data.bundle import load_bundle
from topicpilot_api.research.corporate_action_dataset import (
    CA_EVENT_SCHEMA_VERSION,
    TPEX_BOUNDED_ARTIFACT_REQUIREMENTS,
    CorporateActionDatasetError,
    EpisodeWindow,
    build_coverage_matrix,
    build_event,
    build_identity_coverage_artifact,
    build_identity_coverage_matrix,
    build_owner_bounded_import_envelope,
    build_reviewed_residual_coverage_metadata,
    classify_empty_query,
    dataset_content_hash,
    deduplicate_events,
    evaluate_episode,
    evaluate_freeze_gate,
    export_dataset_document,
    load_dataset,
    merge_owner_bounded_import_into_dataset,
    normalize_official_bounded_csv,
    parse_tpex_bounded_artifact,
    summarize_identity_coverage,
    validate_dataset_document,
    validate_reviewed_residual_coverage_metadata,
)

pytestmark = pytest.mark.research

REPO_ROOT = Path(__file__).resolve().parents[3]
ARTIFACT = (
    REPO_ROOT
    / "reports"
    / "TASK-REC-A1-CORPORATE-ACTION-RESEARCH-DATASET-IMPLEMENTATION"
    / "REC-A1-CA-EVENTS-V0.json"
)
REFERENCE = (
    REPO_ROOT
    / "services"
    / "api"
    / "src"
    / "topicpilot_api"
    / "reference_data"
    / "bundles"
    / "tw-reference-v1"
)


def _document() -> dict:
    return json.loads(ARTIFACT.read_text(encoding="utf-8"))


def _event(*, effective: str, authority: str = "AUTHORITATIVE", reason: str) -> object:
    payload = copy.deepcopy(_document()["events"][0])
    payload.update(
        {
            "source_record_id_or_canonical_row_key": f"fixture-{effective}-{reason}",
            "primary_effective_date": effective,
            "announcement_date_if_available": None,
            "reference_price_if_officially_returned": None,
            "source_content_hash_if_storage_permitted": None,
            "authority_state": authority,
            "reason_code": reason,
        }
    )
    return build_event(payload)


def test_versioned_artifact_loads_against_canonical_reference_bundle():
    stats = load_dataset(ARTIFACT, reference_bundle_dir=REFERENCE)

    assert stats.dataset_rows == 372
    assert stats.twse_rows == 234
    assert stats.tpex_rows == 138
    assert stats.unknown_rows == 0
    assert stats.covered_identities == 353
    assert stats.covered_events == 372
    assert stats.date_range == ("2026-02-05", "2026-08-13")
    assert stats.duplicates == 0
    assert stats.invalid_identities == 0
    assert stats.invalid_effective_dates == 0
    assert stats.missing_lineage == 0
    assert stats.semantic_hash_collisions == 0


def test_control_cases_preserve_identity_and_effective_date_boundaries():
    document = _document()
    by_identity = {event["canonical_identity"]: event for event in document["events"]}
    lifecycle = json.loads(
        (
            REFERENCE / "instrument_lifecycles.json"
        ).read_text(encoding="utf-8")
    )[0]

    control_2330 = by_identity["TPE:2330"]
    assert control_2330["announcement_date_if_available"] is None
    assert control_2330["primary_effective_date"] == "2026-06-11"
    assert control_2330["reason_code"] == "CA_EX_DIVIDEND"
    assert control_2330["canonical_identity"] == "TPE:2330"

    control_6806 = by_identity["TPE:6806"]
    assert control_6806["primary_effective_date"] == "2026-06-23"
    assert control_6806["reason_code"] == "CA_LISTING_TERMINATION"
    assert control_6806["canonical_identity"] == "TPE:6806"
    assert lifecycle["effective_from"] == control_6806["primary_effective_date"]
    assert lifecycle["evidence_id"] == control_6806["source_record_id_or_canonical_row_key"]


def test_export_and_content_hash_are_deterministic_and_raw_ohlcv_is_absent():
    document = _document()
    reordered = copy.deepcopy(document)
    reordered["events"].reverse()
    reordered["manifests"].reverse()
    reordered["checkpoints"].reverse()

    assert dataset_content_hash(document) == dataset_content_hash(reordered)
    assert export_dataset_document(document) == export_dataset_document(reordered)
    assert document["storage_policy"]["raw_source_artifact"] == "NOT_STORED"
    assert all("open" not in event and "close" not in event for event in document["events"])


def test_semantic_hash_and_stable_event_key_reuse_nulls_without_guessing():
    first = _event(effective="2026-06-11", reason="CA_EX_DIVIDEND")
    repeated = _event(effective="2026-06-11", reason="CA_EX_DIVIDEND")

    assert first == repeated
    assert first.semantic_version == CA_EVENT_SCHEMA_VERSION
    assert first.reference_price_if_officially_returned is None
    assert first.source_content_hash_if_storage_permitted is None
    assert first.stable_event_key.endswith("fixture-2026-06-11-CA_EX_DIVIDEND")


def test_duplicate_rerun_reuses_one_semantic_row():
    event = _event(effective="2026-06-11", reason="CA_EX_DIVIDEND")
    unique, duplicates = deduplicate_events((event, event))

    assert len(unique) == 1
    assert duplicates == 1


def test_empty_set_requires_complete_authoritative_query():
    assert (
        classify_empty_query(
            query_completed=True,
            authority_sufficient=True,
            scope_explicit=True,
            response_proves_empty=True,
        )
        == "PASS_NO_EVENT"
    )
    assert (
        classify_empty_query(
            query_completed=False,
            authority_sufficient=True,
            scope_explicit=True,
            response_proves_empty=True,
        )
        == "CA_AUTHORITY_UNKNOWN"
    )
    assert (
        classify_empty_query(
            query_completed=True,
            authority_sufficient=False,
            scope_explicit=True,
            response_proves_empty=True,
        )
        == "CA_AUTHORITY_UNKNOWN"
    )


@pytest.mark.parametrize(
    ("effective", "episode", "expected"),
    [
        (
            "2026-06-03",
            EpisodeWindow(
                date(2026, 6, 1),
                date(2026, 6, 3),
                (date(2026, 6, 4),),
                date(2026, 6, 5),
                (date(2026, 6, 6),),
            ),
            "PRE_SIGNAL_FEATURE_CONTAMINATION",
        ),
        (
            "2026-06-04",
            EpisodeWindow(
                date(2026, 6, 1),
                date(2026, 6, 3),
                (date(2026, 6, 4),),
                date(2026, 6, 5),
                (date(2026, 6, 6),),
            ),
            "TRIGGER_WINDOW_CONTAMINATION",
        ),
        (
            "2026-06-05",
            EpisodeWindow(
                date(2026, 6, 1),
                date(2026, 6, 3),
                (date(2026, 6, 4),),
                date(2026, 6, 5),
                (date(2026, 6, 6),),
            ),
            "EXECUTION_CONTAMINATION",
        ),
        (
            "2026-06-06",
            EpisodeWindow(
                date(2026, 6, 1),
                date(2026, 6, 3),
                (date(2026, 6, 4),),
                date(2026, 6, 5),
                (date(2026, 6, 6),),
            ),
            "OUTCOME_CONTAMINATION",
        ),
    ],
)
def test_overlap_engine_preserves_stage_specific_post_hoc_reasons(
    effective, episode, expected
):
    result = evaluate_episode(
        (_event(effective=effective, reason="CA_EX_DIVIDEND"),),
        episode,
    )

    assert result.excluded is True
    assert result.primary_reason == expected
    assert result.matches[0][1] == "CA_EX_DIVIDEND"


def test_unknown_authority_is_fail_closed_and_never_pass_no_event():
    event = _event(
        effective="2026-06-06",
        authority="UNKNOWN",
        reason="CA_AUTHORITY_UNKNOWN",
    )
    episode = EpisodeWindow(
        date(2026, 6, 1),
        date(2026, 6, 3),
        (),
        date(2026, 6, 5),
        (date(2026, 6, 6),),
    )

    result = evaluate_episode((event,), episode)

    assert result.primary_reason == "OUTCOME_CONTAMINATION"
    assert result.matches == (("OUTCOME_CONTAMINATION", "CA_AUTHORITY_UNKNOWN"),)
    assert (
        classify_empty_query(
            query_completed=False,
            authority_sufficient=False,
            scope_explicit=False,
            response_proves_empty=False,
        )
        == "CA_AUTHORITY_UNKNOWN"
    )


def test_tampered_dataset_identity_fails_closed():
    document = _document()
    document["events"][0]["canonical_identity"] = "TWO:2330"

    with pytest.raises(CorporateActionDatasetError):
        validate_dataset_document(document, reference_bundle_dir=REFERENCE)


def _tpex_artifact(*, records: list[dict] | None = None) -> dict:
    event = copy.deepcopy(_document()["events"][0])
    event.update(
        {
            "source_name": "TPEx",
            "official_product_or_surface": "TPEx ex-right announcement export",
            "access_method": "MANUAL_OR_BOUNDED_QUERY_ONLY",
            "source_url": "https://www.tpex.org.tw/en-us/announce/market/ex/announce.html",
            "source_record_id_or_canonical_row_key": "synthetic-tpex-row-20260611",
            "market_code": "TWO",
            "instrument_code": "1101",
            "canonical_identity": "TWO:1101",
            "event_type": "CASH_DIVIDEND_EX_DIVIDEND",
            "announcement_date_if_available": None,
            "primary_effective_date": "2026-06-11",
            "source_as_of_if_available": None,
            "source_content_hash_if_storage_permitted": None,
            "retrieved_at": "2026-08-15T00:00:00Z",
            "authority_state": "AUTHORITATIVE",
            "query_or_export_manifest_id": "SYNTHETIC-TPEX-MANIFEST",
            "checkpoint_id": "SYNTHETIC-TPEX-CHECKPOINT",
            "reason_code": "CA_EX_DIVIDEND",
        }
    )
    return {
        "artifact_type": "TPEX_BOUNDED_CORPORATE_ACTION_ARTIFACT",
        "source_name": "TPEx",
        "official_surface": "TPEx ex-right announcement export",
        "source_url": "https://www.tpex.org.tw/en-us/announce/market/ex/announce.html",
        "access_method": "MANUAL_OR_BOUNDED_QUERY_ONLY",
        "query_window_start": "2026-02-02",
        "query_window_end": "2026-08-13",
        "event_family_scope": ["CASH_DIVIDEND_EX_DIVIDEND"],
        "security_scope": "TWO:1101",
        "retrieved_at": "2026-08-15T00:00:00Z",
        "manifest_id": "SYNTHETIC-TPEX-MANIFEST",
        "checkpoint_id": "SYNTHETIC-TPEX-CHECKPOINT",
        "records": records if records is not None else [event],
    }


def test_tpex_requirements_are_explicit_without_network_access():
    requirements = TPEX_BOUNDED_ARTIFACT_REQUIREMENTS.to_dict()

    assert requirements["query_date_range"] == {
        "start": "2026-02-02",
        "end": "2026-08-13",
    }
    assert "https://www.tpex.org.tw/en-us/announce/market/ex/announce.html" in requirements[
        "official_surface"
    ]
    assert "primary_effective_date" in requirements["required_fields"]
    assert "announcement_date_if_available" in requirements["optional_fields"]
    assert "CSV_UTF8" in requirements["accepted_file_formats"]
    assert requirements["manual_steps_required"]


def test_tpex_bounded_parser_maps_only_two_identity_and_reuses_existing_schema():
    events = parse_tpex_bounded_artifact(_tpex_artifact())

    assert len(events) == 1
    assert events[0].canonical_identity == "TWO:1101"
    assert events[0].market_code == "TWO"
    assert events[0].semantic_version == CA_EVENT_SCHEMA_VERSION
    assert events[0].primary_effective_date == "2026-06-11"
    assert events[0].announcement_date_if_available is None


def test_tpex_parser_rejects_invalid_identity_and_missing_effective_date():
    invalid_identity = _tpex_artifact()
    invalid_identity["records"][0]["market_code"] = "TPE"
    with pytest.raises(CorporateActionDatasetError, match="market_code must be TWO"):
        parse_tpex_bounded_artifact(invalid_identity)

    missing_date = _tpex_artifact()
    missing_date["records"][0].pop("primary_effective_date")
    with pytest.raises(CorporateActionDatasetError, match="primary_effective_date"):
        parse_tpex_bounded_artifact(missing_date)


def test_tpex_parser_rejects_duplicate_semantic_events():
    artifact = _tpex_artifact()
    artifact["records"] = [artifact["records"][0], copy.deepcopy(artifact["records"][0])]

    with pytest.raises(CorporateActionDatasetError, match="duplicate"):
        parse_tpex_bounded_artifact(artifact)


def test_coverage_matrix_keeps_tpex_partial_with_method_gaps_and_freeze_closed():
    document = _document()
    stats = load_dataset(ARTIFACT, reference_bundle_dir=REFERENCE)
    matrix = build_coverage_matrix(document)

    assert {cell["coverage_state"] for cell in matrix if cell["exchange"] == "TPEx"} == {
        "PARTIAL",
        "UNKNOWN",
    }
    decision = evaluate_freeze_gate(
        matrix,
        stats,
        complete_empty_set_validated=True,
        controls_passed=True,
    )
    assert decision.authorized is False
    assert any(reason.startswith("TPEx:") for reason in decision.reasons)


def test_identity_coverage_does_not_infer_no_event_from_absent_export_rows():
    document = _document()
    matrix = build_identity_coverage_matrix(document, reference_bundle_dir=REFERENCE)
    summary = summarize_identity_coverage(
        matrix,
        outside_scope_rows=1524,
        outside_scope_identities=1125,
    )

    assert len(matrix) == 507 * 8
    assert summary["event_identities"] == 353
    assert summary["covered_identities"] == 353
    assert summary["no_event_identities"] == 0
    assert summary["unknown_identities"] == 154
    assert summary["outside_scope_rows"] == 1524
    assert summary["outside_scope_identities"] == 1125
    assert sum(cell["materialized_rows"] for cell in matrix) == 372
    assert {cell["coverage_state"] for cell in matrix} == {
        "COVERED_EVENT",
        "UNKNOWN",
    }

    stats = load_dataset(ARTIFACT, reference_bundle_dir=REFERENCE)
    decision = evaluate_freeze_gate(
        build_coverage_matrix(document),
        stats,
        complete_empty_set_validated=False,
        controls_passed=True,
        identity_coverage_summary=summary,
    )
    assert decision.authorized is False
    assert "UNKNOWN_IDENTITY_COVERAGE" in decision.reasons


def test_identity_coverage_requires_explicit_empty_set_proof_for_no_event():
    document = _document()
    for coverage in document["source_coverage"].values():
        coverage["complete_empty_set_families"] = [
            "CASH_DIVIDEND_EX_DIVIDEND",
            "STOCK_DIVIDEND_EX_RIGHT",
            "RIGHTS_ISSUE_CAPITAL_INCREASE_REFERENCE_RESET",
            "CAPITAL_REDUCTION",
            "SPLIT_REVERSE_SPLIT_PAR_VALUE_CHANGE",
            "MERGER_SHARE_CONVERSION_DEMERGER",
            "LISTING_TERMINATION_RESUMPTION_DISCONTINUITY",
            "COMBINED_EX_RIGHT_EX_DIVIDEND_SEMANTIC_PARTIAL",
        ]
    matrix = build_identity_coverage_matrix(document, reference_bundle_dir=REFERENCE)
    summary = summarize_identity_coverage(matrix)

    assert summary["event_identities"] == 353
    assert summary["covered_identities"] == 507
    assert summary["no_event_identities"] == 154
    assert summary["unknown_identities"] == 0
    assert sum(cell["materialized_rows"] for cell in matrix) == 372
    assert "COVERED_NO_EVENT" in {cell["coverage_state"] for cell in matrix}


def test_reviewed_residual_uncertainty_is_metadata_only_and_can_pass_freeze_gate():
    document = _document()
    identity_matrix = build_identity_coverage_matrix(document, reference_bundle_dir=REFERENCE)
    summary = summarize_identity_coverage(identity_matrix)
    metadata = build_reviewed_residual_coverage_metadata(
        summary,
        reviewed_unknown_identities=154,
        unreviewed_unknown_identities=0,
        confirmed_additional_event_identities=0,
        authoritative_no_event_identities=0,
        no_event_found_in_bounded_review=True,
        residual_unknown_accepted=True,
        owner_risk_acceptance=True,
        lineage_complete=True,
        fail_closed_outcome_policy_present=True,
        unresolved_confirmed_continuity_events=0,
        dataset_rows_before=372,
        dataset_rows_after=372,
    )
    validate_reviewed_residual_coverage_metadata(metadata)

    stats = load_dataset(ARTIFACT, reference_bundle_dir=REFERENCE)
    decision = evaluate_freeze_gate(
        build_coverage_matrix(document),
        stats,
        complete_empty_set_validated=False,
        controls_passed=True,
        identity_coverage_summary=summary,
        reviewed_residual_metadata=metadata,
    )

    assert metadata["review_state"] == "REVIEWED_UNKNOWN_NO_EVENT_FOUND"
    assert metadata["coverage_summary"]["coverage_states_preserved"] is True
    assert summary["unknown_identities"] == 154
    assert summary["no_event_identities"] == 0
    assert decision.authorized is True
    assert decision.reasons == ()


def test_reviewed_residual_uncertainty_does_not_override_known_integrity_failure():
    document = _document()
    identity_matrix = build_identity_coverage_matrix(document, reference_bundle_dir=REFERENCE)
    summary = summarize_identity_coverage(identity_matrix)
    metadata = build_reviewed_residual_coverage_metadata(
        summary,
        reviewed_unknown_identities=154,
        unreviewed_unknown_identities=0,
        confirmed_additional_event_identities=0,
        authoritative_no_event_identities=0,
        no_event_found_in_bounded_review=True,
        residual_unknown_accepted=True,
        owner_risk_acceptance=True,
        lineage_complete=True,
        fail_closed_outcome_policy_present=True,
        unresolved_confirmed_continuity_events=0,
        dataset_rows_before=372,
        dataset_rows_after=372,
    )
    stats = replace(
        load_dataset(ARTIFACT, reference_bundle_dir=REFERENCE),
        missing_lineage=1,
    )

    decision = evaluate_freeze_gate(
        build_coverage_matrix(document),
        stats,
        complete_empty_set_validated=False,
        controls_passed=True,
        identity_coverage_summary=summary,
        reviewed_residual_metadata=metadata,
    )

    assert decision.authorized is False
    assert "DATASET_VALIDATION_ERRORS" in decision.reasons


def test_coverage_artifact_is_metadata_only_and_hashable():
    artifact = build_identity_coverage_artifact(
        _document(),
        reference_bundle_dir=REFERENCE,
        outside_scope_rows=1524,
        outside_scope_identities=1125,
    )

    assert artifact["artifact_type"] == "REC_A1_IDENTITY_EVENT_FAMILY_WINDOW_COVERAGE_V0"
    assert artifact["summary"]["unknown_identities"] == 154
    assert artifact["summary"]["no_event_identities"] == 0
    assert artifact["outside_scope"]["coverage_state"] == "OUTSIDE_SCOPE"
    assert artifact["outside_scope"]["rows"] == 1524
    assert artifact["coverage_content_hash"]
    assert all("raw" not in key.lower() for key in artifact)


def test_freeze_gate_refuses_partial_twse_even_if_tpex_is_closed():
    document = _document()
    stats = load_dataset(ARTIFACT, reference_bundle_dir=REFERENCE)
    matrix = tuple(
        {
            **cell,
            "coverage_state": "COMPLETE"
            if cell["exchange"] == "TPEx"
            else cell["coverage_state"],
        }
        for cell in build_coverage_matrix(document)
    )
    decision = evaluate_freeze_gate(
        matrix,
        replace(stats, covered_identities=507),
        complete_empty_set_validated=True,
        controls_passed=True,
    )

    assert decision.authorized is False
    assert any(reason.startswith("TWSE:") for reason in decision.reasons)


def test_owner_bounded_csv_normalization_splits_explicit_tpex_components_and_keeps_outside(
    tmp_path,
):
    tpe_code = next(
        row["instrument_code"]
        for row in load_bundle(REFERENCE).instruments
        if row["market_code"] == "TPE"
    )
    twse_path = tmp_path / "TWT49U.csv"
    twse_path.write_text(
        "\n".join(
            [
                "title",
                "date,code,name,pre,reference,value,type,upper,lower",
                f"115年05月06日,=\"{tpe_code}\",canonical,10,9.5,0.5,權息,10,1",
                "115年05月07日,=\"9999\",outside,10,9.5,0.5,息,10,1",
            ]
        )
        + "\n",
        encoding="utf-8-sig",
    )
    tpex_code = next(
        row["instrument_code"]
        for row in load_bundle(REFERENCE).instruments
        if row["market_code"] == "TWO"
    )
    tpex_path = tmp_path / "Exright.csv"
    tpex_path.write_text(
        "\n".join(
            [
                "title",
                "scope",
                "date,code,name,pre,reference,right,interest,total,type,up,down,open,cash,stock,capital,subscription,public,employee,original,holder",
                f"115/05/06,{tpex_code},canonical,10,9.5,1,2,3,除權息,10,1,9.5,9.5,2,5,0,0,0,0,0,0",
                f"115/05/07,{tpex_code},canonical,10,9.5,1,0,1,除權,10,1,9.5,9.5,0,0,100,20,0,0,0,0",
            ]
        )
        + "\n",
        encoding="utf-8-sig",
    )

    twse = normalize_official_bounded_csv(
        twse_path,
        source_name="TWSE",
        source_url="https://www.twse.com.tw/en/announcement/ex-right/twt49u.html",
        official_surface="TWSE TWT49U bounded CSV",
        encoding="utf-8-sig",
        retrieved_at="2026-08-15T00:00:00Z",
        manifest_id="TEST-TWSE-MANIFEST",
        checkpoint_id="TEST-TWSE-CHECKPOINT",
        reference_bundle_dir=REFERENCE,
    )
    tpex = normalize_official_bounded_csv(
        tpex_path,
        source_name="TPEx",
        source_url="https://www.tpex.org.tw/en-us/announce/market/ex/cal.html",
        official_surface="TPEx bounded CSV",
        encoding="utf-8-sig",
        retrieved_at="2026-08-15T00:00:00Z",
        manifest_id="TEST-TPEX-MANIFEST",
        checkpoint_id="TEST-TPEX-CHECKPOINT",
        reference_bundle_dir=REFERENCE,
    )

    assert (twse.raw_row_count, twse.canonical_source_rows, twse.outside_rows) == (2, 1, 1)
    assert [event.event_type for event in twse.events] == [
        "COMBINED_EX_RIGHT_EX_DIVIDEND_SEMANTIC_PARTIAL"
    ]
    assert (tpex.raw_row_count, tpex.canonical_source_rows, len(tpex.events)) == (2, 2, 3)
    assert {event.event_type for event in tpex.events} == {
        "CASH_DIVIDEND_EX_DIVIDEND",
        "STOCK_DIVIDEND_EX_RIGHT",
        "RIGHTS_ISSUE_CAPITAL_INCREASE_REFERENCE_RESET",
    }
    assert len(twse.outside_audit_rows) == 1
    assert twse.outside_audit_rows[0]["classification"] == "OUTSIDE_CANONICAL_507"
    assert len(parse_tpex_bounded_artifact(tpex.to_envelope())) == 3

    envelope = build_owner_bounded_import_envelope((twse, tpex))
    assert envelope["canonical_record_count"] == 4
    assert envelope["outside_audit_row_count"] == 1
    assert envelope["import_content_hash"]


def test_owner_import_merge_replaces_same_semantic_prior_row_and_preserves_lifecycle():
    document = _document()
    event = copy.deepcopy(document["events"][0])
    event["source_name"] = "TWSE"
    event["official_product_or_surface"] = "TWSE TWT49U bounded CSV"
    event["source_url"] = "https://www.twse.com.tw/en/announcement/ex-right/twt49u.html"
    event["source_record_id_or_canonical_row_key"] = (
        "TWSE:BOUNDED_CSV:ROW:3:CASH_DIVIDEND_EX_DIVIDEND"
    )
    event["query_or_export_manifest_id"] = "TEST-TWSE-MANIFEST"
    event["checkpoint_id"] = "TEST-TWSE-CHECKPOINT"
    event = build_event(event)
    checkpoint_base = {
        "checkpoint_id": "TEST-TWSE-CHECKPOINT",
        "manifest_id": "TEST-TWSE-MANIFEST",
        "dataset_version": "REC-A1-CA-EVENTS-V0",
        "event_keys": [event.stable_event_key],
        "status": "COMPLETED",
    }
    owner = {
        "artifact_type": "OWNER_BOUNDED_CORPORATE_ACTION_IMPORT_V0",
        "import_content_hash": "",
        "records": [event.to_dict()],
        "sources": [
            {
                "source_name": "TWSE",
                "raw_row_count": 1,
                "canonical_source_rows": 1,
                "canonical_identities": 1,
                "outside_rows": 0,
                "outside_identities": 0,
            }
        ],
        "manifests": [
            {
                "manifest_id": "TEST-TWSE-MANIFEST",
                "source_name": "TWSE",
                "source_method": "MANUAL_OR_BOUNDED_QUERY_ONLY",
                "official_surface": "TWSE TWT49U bounded CSV",
                "query_window_start": "2026-02-02",
                "query_window_end": "2026-08-13",
                "retrieved_at": "2026-08-15T00:00:00Z",
                "source_as_of_if_available": None,
                "record_count": 1,
                "content_hash_if_allowed": None,
                "semantic_version": "CA-EVENT-SCHEMA-V0",
                "reference_version": "tw-reference-v1",
                "status": "PARTIAL",
            }
        ],
        "checkpoints": [{**checkpoint_base, "checkpoint_hash": ""}],
    }
    owner["checkpoints"][0]["checkpoint_hash"] = stable_hash(checkpoint_base)
    owner["import_content_hash"] = stable_hash(
        {key: value for key, value in owner.items() if key != "import_content_hash"}
    )

    merged = merge_owner_bounded_import_into_dataset(document, owner)
    identities = {row["canonical_identity"] for row in merged["events"]}
    assert "TPE:6806" in identities
    assert sum(
        row["canonical_identity"] == event.canonical_identity
        for row in merged["events"]
    ) == 1
