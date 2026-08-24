"""Disposable PostgreSQL E2E for formal Today/Home V2 publication.

This script is test-only plumbing.  It seeds a small formal topic evidence
surface and explicit TEST_ONLY_SYNTHETIC_FORMAL_FIXTURE market authorities;
it never calls a production endpoint or provider.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from topicpilot_api.home_read_model import build_home_read_model
from topicpilot_api.home_v2_publication import materialize_home_v2
from topicpilot_api.reference_data import load_bundle
from topicpilot_api.reference_data.bootstrap import bootstrap_reference_bundle
from topicpilot_api.schemas import HomeResponse

REFERENCE_VERSION = "tw-reference-v1"
TARGET_DATE = date(2026, 8, 21)
AS_OF = datetime(2026, 8, 21, 16, 0, tzinfo=UTC)
FIXTURE_RUN_ID = "TEST_ONLY_SYNTHETIC_FORMAL_FIXTURE:home-v2:20260821"
BUNDLE_PATH = (
    __import__("pathlib").Path(__file__).parents[1]
    / "src"
    / "topicpilot_api"
    / "reference_data"
    / "bundles"
    / "tw-reference-v1"
)


def _seed_formal_topics(session: Session) -> None:
    for rank, (slug, name) in enumerate(
        (
            ("fixture-alpha", "Fixture Alpha"),
            ("fixture-beta", "Fixture Beta"),
            ("fixture-gamma", "Fixture Gamma"),
        )
    ):
        session.execute(
            text(
                """
                INSERT INTO topicpilot.topics (
                    id, slug, name, description, status, dictionary_version,
                    valid_from, display_metadata
                ) VALUES (
                    :id, :slug, :name, 'TEST_ONLY_SYNTHETIC_FORMAL_FIXTURE',
                    'ACTIVE', 'home-v2-fixture.v1', :valid_from,
                    CAST(:display_metadata AS jsonb)
                ) ON CONFLICT (slug) DO NOTHING
                """
            ),
            {
                "id": uuid.uuid5(uuid.NAMESPACE_URL, f"{FIXTURE_RUN_ID}:catalog:{rank}"),
                "slug": slug,
                "name": name,
                "valid_from": date(2026, 8, 7),
                "display_metadata": json.dumps({"fixtureTestOnly": True}),
            },
        )
    topics = session.execute(
        text(
            """
            SELECT id, slug, name, NULL::text AS parent_topic
            FROM topicpilot.topics
            WHERE status NOT IN ('DISABLED', 'RETIRED')
            ORDER BY slug
            LIMIT 3
            """
        )
    ).mappings().all()
    if len(topics) != 3:
        raise RuntimeError(f"expected three enabled topics, got {len(topics)}")
    for rank, topic in enumerate(topics):
        session.execute(
            text(
                """
                INSERT INTO topicpilot.topic_snapshots (
                    id, snapshot_date, topic_id, topic_slug, topic_name,
                    parent_topic, market_grade, topic_score, topic_direction,
                    stock_count, strong_stock_count, weak_stock_count,
                    average_change, observed_stock_count, coverage_pct,
                    data_status, score_status, calculation_version, metadata,
                    publication_mode, membership_mode, relation_version,
                    mapping_effective_from, membership_snapshot_id,
                    membership_snapshot_hash, session_code, calendar_code,
                    trading_day_state, generated_state, finality_state,
                    publication_state, generated_at, as_of_at, finalized_at,
                    published_at, expected_count, eligible_count, no_trade_count,
                    unknown_count, excluded_count, positive_count, flat_count,
                    negative_count, freshness_state, quality_flags,
                    reference_registry_version, mapping_policy_version,
                    source_run_id, source_artifact_id, source_artifact_hash,
                    lineage_hash, snapshot_identity, correction_sequence
                ) VALUES (
                    :id, :snapshot_date, :topic_id, :topic_slug, :topic_name,
                    :parent_topic, :market_grade, :topic_score, :topic_direction,
                    :stock_count, :strong_stock_count, :weak_stock_count,
                    :average_change, :observed_stock_count, :coverage_pct,
                    'COMPLETE', 'AVAILABLE', 'home-v2-fixture.v1', CAST(:metadata AS jsonb),
                    'FORMAL', 'PIT_FORMAL', 'home-v2-fixture-relation.v1',
                    :mapping_effective_from, :membership_snapshot_id,
                    :membership_snapshot_hash, 'REGULAR', 'TWSE_TPEX',
                    'TRADING', 'GENERATED', 'FINAL', 'PUBLISHED',
                    :generated_at, :as_of_at, :finalized_at, :published_at,
                    :expected_count, :eligible_count, 0, 0, 0,
                    :positive_count, 0, 0, 'FRESH', CAST(:quality_flags AS jsonb),
                    :reference_registry_version, 'home-v2-fixture-mapping.v1',
                    :source_run_id, 'TEST_ONLY_SYNTHETIC_FORMAL_FIXTURE',
                    :source_artifact_hash, :lineage_hash, :snapshot_identity, 0
                )
                ON CONFLICT (snapshot_identity) DO NOTHING
                """
            ),
            {
                "id": uuid.uuid5(uuid.NAMESPACE_URL, f"{FIXTURE_RUN_ID}:topic:{rank}"),
                "snapshot_date": TARGET_DATE,
                "topic_id": topic["id"],
                "topic_slug": topic["slug"],
                "topic_name": topic["name"],
                "parent_topic": topic["parent_topic"],
                "market_grade": ("A", "B", "S")[rank],
                "topic_score": Decimal(90 - rank),
                "topic_direction": "UP",
                "stock_count": 10 + rank,
                "strong_stock_count": 4,
                "weak_stock_count": 1,
                "average_change": Decimal("2.5") - Decimal(rank) / Decimal(10),
                "observed_stock_count": 8 - rank,
                "coverage_pct": Decimal(80 - rank * 5),
                "positive_count": 5 - rank,
                "mapping_effective_from": date(2026, 8, 7),
                "membership_snapshot_id": "home-v2-fixture-membership-v1",
                "membership_snapshot_hash": "a" * 64,
                "generated_at": AS_OF,
                "as_of_at": AS_OF,
                "finalized_at": AS_OF,
                "published_at": AS_OF,
                "expected_count": 10 + rank,
                "eligible_count": 8 - rank,
                "reference_registry_version": REFERENCE_VERSION,
                "source_run_id": FIXTURE_RUN_ID,
                "source_artifact_hash": "b" * 64,
                "lineage_hash": "c" * 64,
                "snapshot_identity": f"{FIXTURE_RUN_ID}:topic:{topic['slug']}",
                "quality_flags": json.dumps({"fixtureTestOnly": True}),
                "metadata": json.dumps({"fixtureTestOnly": True, "rankSeed": rank}),
            },
        )


def _index_facts() -> list[dict[str, object]]:
    return [
        {
            "market": "TPE",
            "indexCode": "TWSE:TAIEX",
            "indexName": "TWSE 加權指數",
            "tradingDate": TARGET_DATE,
            "session": "CLOSE",
            "value": Decimal("22450.10"),
            "previousClose": Decimal("22380.00"),
            "change": Decimal("70.10"),
            "changePct": Decimal("0.31"),
            "asOf": AS_OF,
            "source": "TEST_ONLY_SYNTHETIC_FORMAL_FIXTURE:TWSE",
            "lineage": "TEST_ONLY_SYNTHETIC_FORMAL_FIXTURE -> TWSE official index contract",
            "status": "AVAILABLE",
        },
        {
            "market": "TWO",
            "indexCode": "TPEX:TPEx",
            "indexName": "TPEx 櫃買指數",
            "tradingDate": TARGET_DATE,
            "session": "CLOSE",
            "value": Decimal("245.20"),
            "previousClose": Decimal("244.10"),
            "change": Decimal("1.10"),
            "changePct": Decimal("0.45"),
            "asOf": AS_OF,
            "source": "TEST_ONLY_SYNTHETIC_FORMAL_FIXTURE:TPEx",
            "lineage": "TEST_ONLY_SYNTHETIC_FORMAL_FIXTURE -> TPEx official index contract",
            "status": "AVAILABLE",
        },
    ]


def _aggregate_facts() -> list[dict[str, object]]:
    common = {
        "tradingDate": TARGET_DATE,
        "currency": "TWD",
        "turnoverUnit": "TWD",
        "turnoverScale": 0,
        "asOf": AS_OF,
        "status": "AVAILABLE",
        "source": "TEST_ONLY_SYNTHETIC_FORMAL_FIXTURE",
        "lineage": "TEST_ONLY_SYNTHETIC_FORMAL_FIXTURE -> official whole-market aggregate contract",
    }
    return [
        {
            **common,
            "market": "TPE",
            "turnover": Decimal("711182569693"),
            "eligible": 1074,
            "observed": 1070,
            "advancers": 589,
            "decliners": 381,
            "unchanged": 104,
            "unavailable": 4,
            "limitUpCount": 14,
            "limitDownCount": 2,
        },
        {
            **common,
            "market": "TWO",
            "turnover": Decimal("198448672072"),
            "eligible": 890,
            "observed": 874,
            "advancers": 414,
            "decliners": 380,
            "unchanged": 80,
            "unavailable": 16,
            "limitUpCount": 9,
            "limitDownCount": 6,
        },
    ]


def run(database_url: str) -> dict[str, object]:
    engine = create_engine(database_url, pool_pre_ping=True)
    with Session(engine) as session:
        bundle = load_bundle(BUNDLE_PATH)
        bootstrap_reference_bundle(session, bundle, activate=True)
        _seed_formal_topics(session)
        session.commit()

    with Session(engine) as session:
        first = materialize_home_v2(
            session,
            trading_date=TARGET_DATE,
            source_run_id=FIXTURE_RUN_ID,
            market_index_facts=_index_facts(),
            market_aggregate_facts=_aggregate_facts(),
            now=AS_OF,
        )
    with Session(engine) as session:
        second = materialize_home_v2(
            session,
            trading_date=TARGET_DATE,
            source_run_id=FIXTURE_RUN_ID,
            market_index_facts=_index_facts(),
            market_aggregate_facts=_aggregate_facts(),
            now=AS_OF,
        )
        response = build_home_read_model(session, now=AS_OF)
        HomeResponse.model_validate(response)
        counts = {
            "homePublications": session.scalar(
                text("SELECT count(*) FROM topicpilot.home_publications")
            ),
            "homePublicationSections": session.scalar(
                text("SELECT count(*) FROM topicpilot.home_publication_sections")
            ),
            "homeMarketFacts": session.scalar(
                text("SELECT count(*) FROM topicpilot.home_market_facts")
            ),
            "formalTopicSnapshots": session.scalar(
                text(
                    "SELECT count(*) FROM topicpilot.topic_snapshots "
                    "WHERE publication_mode='FORMAL' AND publication_state='PUBLISHED'"
                )
            ),
        }

    return {
        "fixture": "TEST_ONLY_SYNTHETIC_FORMAL_FIXTURE",
        "tradingDate": TARGET_DATE.isoformat(),
        "first": first,
        "second": second,
        "response": response,
        "counts": counts,
        "assertions": {
            "published": first["publicationState"] == "PUBLISHED",
            "secondMaterializationIdempotent": second["status"] == "IDEMPOTENT",
            "noDuplicatePublication": counts["homePublications"] == 1,
            "marketOverviewAvailable": response["marketOverview"]["dataStatus"] == "AVAILABLE",
            "dailyFocusAvailable": (
                response["sectionStatuses"]["dailyFocus"]["status"] == "AVAILABLE"
            ),
            "mainTopicsAvailable": (
                response["sectionStatuses"]["mainTopics"]["status"] == "AVAILABLE"
            ),
            "apiReadsFormalPublication": response["publication"]["state"] == "PUBLISHED",
        },
    }


if __name__ == "__main__":
    print(json.dumps(run(os.environ["DATABASE_URL"]), ensure_ascii=False, default=str, indent=2))
