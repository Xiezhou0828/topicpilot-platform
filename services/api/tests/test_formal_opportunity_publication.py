from __future__ import annotations

from datetime import date

from topicpilot_api.formal_opportunity_publication import (
    FORMAL_OPPORTUNITY_AUTHORITY_VERSION,
    build_deferred_formal_opportunity_package,
    build_formal_opportunity_package,
)
from topicpilot_api.formal_opportunity_universe import (
    FormalOpportunityUniverseReadModel,
)


def _universe(status: str) -> FormalOpportunityUniverseReadModel:
    return FormalOpportunityUniverseReadModel(
        contract_version="opportunity-formal-topic-universe.v1",
        as_of=date(2026, 9, 20),
        status=status,
        publication_status="FORMAL",
        source_status="FORMAL_CANONICAL",
        topic_entity_level="LEAF",
        full_topic_universe=True,
        publishable=status in {"READY", "ZERO_VALID_CANDIDATES"},
        expected_topic_count=1,
        available_topic_count=1,
        eligible_topic_count=1,
        ineligible_topic_count=0,
        unavailable_topic_count=0,
        member_relation_count=0,
        unique_instrument_count=0,
        excluded_relation_count=0,
        instruments=(),
        unavailable_topic_ids=(),
        excluded_relation_reasons=(),
        price_boundary_status="NOT_REQUESTED",
        leader_status="UNAVAILABLE_NOT_GATING",
        strategy_status="NOT_RUN",
        selector_status="NOT_RUN",
        c1_c5_status="UNCHANGED_NOT_EXECUTED",
        s1_s2_status="UNCHANGED_NOT_EXECUTED",
        fund_c_status="EVIDENCE_ONLY_NOT_CONSUMED",
        reasons=(),
    )


def test_deferred_package_is_deterministic_and_does_not_invent_cards():
    first = build_deferred_formal_opportunity_package(_universe("READY"))
    second = build_deferred_formal_opportunity_package(_universe("READY"))

    assert first.publication_state == "DEFERRED"
    assert first.lineage_hash == second.lineage_hash
    assert first.page_payload["sections"] == []
    assert first.page_payload["sourceStatus"] == "FORMAL_CANONICAL"
    assert first.authority_version == FORMAL_OPPORTUNITY_AUTHORITY_VERSION


def test_zero_candidate_package_is_formal_empty_not_unavailable():
    package = build_deferred_formal_opportunity_package(
        _universe("ZERO_VALID_CANDIDATES")
    )

    assert package.publication_state == "EMPTY"
    assert package.page_payload["state"] == "EMPTY"
    assert package.page_payload["publicationStatus"] == "FORMAL"


def test_formal_package_normalizes_a_deferred_page():
    page = {
        "contractVersion": "opportunity-page-read.v1",
        "state": "DEFERRED",
        "publicationStatus": "FORMAL",
        "dataStatus": "FORMAL_UNIVERSE_READY",
        "sourceStatus": "FORMAL_CANONICAL",
        "asOf": "2026-09-20",
        "updatedAt": "2026-09-20T00:00:00Z",
        "sectionMappingStatus": "UNAVAILABLE",
        "providerLineage": {
            "provider": "formal-opportunity-provider",
            "authority": "FORMAL_OPPORTUNITY_AUTHORITY",
            "contractVersion": "opportunity-page-read.v1",
            "sourceArtifactId": "universe:2026-09-20",
            "sourceArtifactHash": "hash",
            "policyVersion": "opportunity-formal-authority-20260920.v1",
        },
        "sections": [],
    }
    package = build_formal_opportunity_package(
        as_of=date(2026, 9, 20),
        page_payload=page,
        source_artifact_id="universe:2026-09-20",
        source_artifact_hash="hash",
    )

    assert package.publication_state == "DEFERRED"
    assert package.page_payload["state"] == "DEFERRED"

