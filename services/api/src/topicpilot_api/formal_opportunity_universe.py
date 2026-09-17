"""Formal, read-only Opportunity Topic-universe consumer.

This module stops at the deduplicated formal Topic universe boundary.  It
consumes point-in-time Topic state, an explicit formal eligibility decision,
and date-effective approved relations.  It deliberately does not calculate
Grade/Lifecycle policy, Leader membership, C1-C5, Strategy, Selector, or
FUND-C effects.  Those contracts are separate downstream authorities and are
reported as unavailable/not-run until their formal publication is approved.

The consumer is intentionally independent of the shadow Opportunity modules.
Shadow, research, fixture, and future-dated records cannot be promoted by
this read model.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any

CONTRACT_VERSION = "opportunity-formal-topic-universe.v1"
FORMAL_PUBLICATION_STATUS = "FORMAL"
UNAVAILABLE_PUBLICATION_STATUS = "UNAVAILABLE"
FORMAL_SOURCE_STATUS = "FORMAL_CANONICAL"
UNAVAILABLE_SOURCE_STATUS = "UNAVAILABLE"
FORMAL_TOPIC_LEVEL = "LEAF"
APPROVED_RELATION_STATE = "APPROVED"
ACTIVE_INSTRUMENT_STATE = "ACTIVE"
ELIGIBLE = "ELIGIBLE"
INELIGIBLE = "INELIGIBLE"
UNAVAILABLE = "UNAVAILABLE"
OWNER_DECISION_REQUIRED = "OWNER_DECISION_REQUIRED"
READY = "READY"
ZERO_VALID_CANDIDATES = "ZERO_VALID_CANDIDATES"
PARTIAL = "PARTIAL"
PRICE_NOT_REQUESTED = "NOT_REQUESTED"
PRICE_AVAILABLE = "AVAILABLE"
PRICE_UNAVAILABLE = "UNAVAILABLE"
NOT_RUN = "NOT_RUN"
UNCHANGED_NOT_EXECUTED = "UNCHANGED_NOT_EXECUTED"
EVIDENCE_ONLY_NOT_CONSUMED = "EVIDENCE_ONLY_NOT_CONSUMED"

_FORBIDDEN_SOURCE_TOKENS = (
    "SHADOW",
    "RESEARCH",
    "FIXTURE",
    "DEMO",
)
_ALLOWED_MARKETS = frozenset({"TPE", "TWO"})
_EXCLUDED_INSTRUMENT_STATES = frozenset({"DELISTED", "TERMINATED", "SUSPENDED"})


class FormalOpportunityUniverseError(ValueError):
    """Raised when a formal universe input is structurally unsafe to read."""


def _contains_forbidden_source(value: str) -> bool:
    normalized = value.strip().upper()
    return any(token in normalized for token in _FORBIDDEN_SOURCE_TOKENS)


def _require_text(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise FormalOpportunityUniverseError(f"{field} is required")


def _require_formal_or_unavailable(value: str, field: str) -> None:
    _require_text(value, field)
    if _contains_forbidden_source(value):
        raise FormalOpportunityUniverseError(f"{field} cannot be shadow/research/fixture data")


@dataclass(frozen=True)
class FormalTopicState:
    """One formally published Topic daily state at exactly one as-of date."""

    topic_id: str
    slug: str
    name: str
    topic_type: str
    as_of: date
    publication_status: str
    data_status: str
    snapshot_id: str
    snapshot_hash: str
    source_version: str = "topic-daily-state.v1"
    freshness: str = "EXACT_AS_OF"
    daily_strength: Decimal | None = None
    topic_score: Decimal | None = None
    grade: str | None = None
    lifecycle_stage: str | None = None
    expected_member_count: int = 0
    eligible_member_count: int = 0

    def __post_init__(self) -> None:
        for field, value in (
            ("topic_id", self.topic_id),
            ("slug", self.slug),
            ("name", self.name),
            ("snapshot_id", self.snapshot_id),
            ("snapshot_hash", self.snapshot_hash),
        ):
            _require_text(value, field)
        _require_formal_or_unavailable(self.publication_status, "publication_status")
        _require_formal_or_unavailable(self.data_status, "data_status")
        _require_formal_or_unavailable(self.source_version, "source_version")
        if self.topic_type not in {"LEAF", "PARENT"}:
            raise FormalOpportunityUniverseError("topic_type must be LEAF or PARENT")
        if self.freshness != "EXACT_AS_OF":
            raise FormalOpportunityUniverseError(
                "formal Topic state requires EXACT_AS_OF freshness"
            )
        if self.expected_member_count < 0 or self.eligible_member_count < 0:
            raise FormalOpportunityUniverseError("Topic member counts cannot be negative")


@dataclass(frozen=True)
class FormalTopicEligibility:
    """An externally approved decision; this consumer never derives it."""

    topic_id: str
    status: str
    as_of: date
    policy_version: str
    authority_source: str
    reason: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.topic_id, "topic_id")
        _require_text(self.policy_version, "policy_version")
        _require_formal_or_unavailable(self.authority_source, "authority_source")
        if self.status in {ELIGIBLE, INELIGIBLE} and self.authority_source.upper() == UNAVAILABLE:
            raise FormalOpportunityUniverseError(
                "eligible/ineligible Topic decisions require an available authority source"
            )
        if self.status not in {ELIGIBLE, INELIGIBLE, UNAVAILABLE, OWNER_DECISION_REQUIRED}:
            raise FormalOpportunityUniverseError("unsupported Topic eligibility status")


@dataclass(frozen=True)
class FormalTopicMemberRelation:
    """A date-effective relation candidate from formal Topic authority."""

    relation_id: str
    topic_id: str
    instrument_id: str
    instrument_code: str
    instrument_name: str
    market_code: str
    relation_type: str
    approval_state: str
    valid_from: date
    valid_to: date | None = None
    instrument_type: str = "EQUITY"
    instrument_status: str = ACTIVE_INSTRUMENT_STATE
    publication_status: str = FORMAL_PUBLICATION_STATUS
    relation_version: str = "topic-membership-pit.v1"
    source_artifact_id: str = "formal-topic-membership"
    source_artifact_hash: str = "sha256:formal-topic-membership"
    lineage_hash: str = "sha256:formal-topic-membership-lineage"
    structural_role: str | None = None
    role_authority_version: str | None = None
    role_authority_hash: str | None = None
    role_lineage_hash: str | None = None

    def __post_init__(self) -> None:
        for field, value in (
            ("relation_id", self.relation_id),
            ("topic_id", self.topic_id),
            ("instrument_id", self.instrument_id),
            ("instrument_code", self.instrument_code),
            ("instrument_name", self.instrument_name),
            ("market_code", self.market_code),
            ("relation_type", self.relation_type),
            ("approval_state", self.approval_state),
            ("relation_version", self.relation_version),
            ("source_artifact_id", self.source_artifact_id),
            ("source_artifact_hash", self.source_artifact_hash),
            ("lineage_hash", self.lineage_hash),
        ):
            _require_text(value, field)
        _require_formal_or_unavailable(self.publication_status, "publication_status")
        if self.valid_to is not None and self.valid_to < self.valid_from:
            raise FormalOpportunityUniverseError("relation valid_to cannot precede valid_from")


@dataclass(frozen=True)
class FormalPriceObservation:
    """Optional exact-date price boundary for downstream technical stages."""

    instrument_id: str
    as_of: date
    status: str
    close: Decimal | None = None
    observation_id: str | None = None
    publication_status: str = FORMAL_PUBLICATION_STATUS

    def __post_init__(self) -> None:
        _require_text(self.instrument_id, "instrument_id")
        _require_formal_or_unavailable(self.publication_status, "publication_status")
        if self.status not in {"AVAILABLE", "NO_TRADE", "UNKNOWN", "UNAVAILABLE"}:
            raise FormalOpportunityUniverseError("unsupported price observation status")
        if self.status == "AVAILABLE" and self.publication_status != FORMAL_PUBLICATION_STATUS:
            raise FormalOpportunityUniverseError(
                "available price observation requires formal publication"
            )
        if self.status == "AVAILABLE" and self.close is None:
            raise FormalOpportunityUniverseError("available price observation requires close")


@dataclass(frozen=True)
class FormalInstrumentMember:
    """One deduplicated instrument with all Topic provenance retained."""

    instrument_id: str
    instrument_code: str
    instrument_name: str
    market_code: str
    topic_ids: tuple[str, ...]
    topic_slugs: tuple[str, ...]
    topic_names: tuple[str, ...]
    relation_ids: tuple[str, ...]
    relation_types: tuple[str, ...]
    structural_roles: tuple[str, ...]
    price_status: str = PRICE_NOT_REQUESTED

    def to_dict(self) -> dict[str, Any]:
        return {
            "instrumentId": self.instrument_id,
            "instrumentCode": self.instrument_code,
            "instrumentName": self.instrument_name,
            "marketCode": self.market_code,
            "topicIds": list(self.topic_ids),
            "topicSlugs": list(self.topic_slugs),
            "topicNames": list(self.topic_names),
            "relationIds": list(self.relation_ids),
            "relationTypes": list(self.relation_types),
            "structuralRoles": list(self.structural_roles),
            "priceStatus": self.price_status,
        }


@dataclass(frozen=True)
class FormalOpportunityUniverseReadModel:
    """Read-only output before any Strategy/Selector or page publication."""

    contract_version: str
    as_of: date
    status: str
    publication_status: str
    source_status: str
    topic_entity_level: str
    full_topic_universe: bool
    publishable: bool
    expected_topic_count: int
    available_topic_count: int
    eligible_topic_count: int
    ineligible_topic_count: int
    unavailable_topic_count: int
    member_relation_count: int
    unique_instrument_count: int
    excluded_relation_count: int
    instruments: tuple[FormalInstrumentMember, ...]
    unavailable_topic_ids: tuple[str, ...]
    excluded_relation_reasons: tuple[tuple[str, int], ...]
    price_boundary_status: str
    leader_status: str
    strategy_status: str
    selector_status: str
    c1_c5_status: str
    s1_s2_status: str
    fund_c_status: str
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "contractVersion": self.contract_version,
            "asOf": self.as_of.isoformat(),
            "status": self.status,
            "publicationStatus": self.publication_status,
            "sourceStatus": self.source_status,
            "topicEntityLevel": self.topic_entity_level,
            "fullTopicUniverse": self.full_topic_universe,
            "publishable": self.publishable,
            "counts": {
                "expectedTopics": self.expected_topic_count,
                "availableTopics": self.available_topic_count,
                "eligibleTopics": self.eligible_topic_count,
                "ineligibleTopics": self.ineligible_topic_count,
                "unavailableTopics": self.unavailable_topic_count,
                "memberRelations": self.member_relation_count,
                "uniqueInstruments": self.unique_instrument_count,
                "excludedRelations": self.excluded_relation_count,
            },
            "instruments": [item.to_dict() for item in self.instruments],
            "unavailableTopicIds": list(self.unavailable_topic_ids),
            "excludedRelationReasons": [
                {"reason": reason, "count": count}
                for reason, count in self.excluded_relation_reasons
            ],
            "priceBoundaryStatus": self.price_boundary_status,
            "leaderStatus": self.leader_status,
            "strategyStatus": self.strategy_status,
            "selectorStatus": self.selector_status,
            "c1C5Status": self.c1_c5_status,
            "s1S2Status": self.s1_s2_status,
            "fundCStatus": self.fund_c_status,
            "reasons": list(self.reasons),
        }


def _empty_result(
    *,
    as_of: date,
    status: str,
    expected_topic_count: int,
    available_topic_count: int = 0,
    eligible_topic_count: int = 0,
    ineligible_topic_count: int = 0,
    unavailable_topic_count: int = 0,
    unavailable_topic_ids: tuple[str, ...] = (),
    reasons: tuple[str, ...] = (),
    full_topic_universe: bool = False,
    publishable: bool = False,
    publication_status: str = UNAVAILABLE_PUBLICATION_STATUS,
    source_status: str = UNAVAILABLE_SOURCE_STATUS,
    member_relation_count: int = 0,
    unique_instrument_count: int = 0,
    excluded_relation_count: int = 0,
    instruments: tuple[FormalInstrumentMember, ...] = (),
    excluded_relation_reasons: tuple[tuple[str, int], ...] = (),
    price_boundary_status: str = PRICE_NOT_REQUESTED,
) -> FormalOpportunityUniverseReadModel:
    return FormalOpportunityUniverseReadModel(
        contract_version=CONTRACT_VERSION,
        as_of=as_of,
        status=status,
        publication_status=publication_status,
        source_status=source_status,
        topic_entity_level=FORMAL_TOPIC_LEVEL,
        full_topic_universe=full_topic_universe,
        publishable=publishable,
        expected_topic_count=expected_topic_count,
        available_topic_count=available_topic_count,
        eligible_topic_count=eligible_topic_count,
        ineligible_topic_count=ineligible_topic_count,
        unavailable_topic_count=unavailable_topic_count,
        member_relation_count=member_relation_count,
        unique_instrument_count=unique_instrument_count,
        excluded_relation_count=excluded_relation_count,
        instruments=instruments,
        unavailable_topic_ids=unavailable_topic_ids,
        excluded_relation_reasons=excluded_relation_reasons,
        price_boundary_status=price_boundary_status,
        leader_status="UNAVAILABLE_NOT_GATING",
        strategy_status=NOT_RUN,
        selector_status=NOT_RUN,
        c1_c5_status=UNCHANGED_NOT_EXECUTED,
        s1_s2_status=UNCHANGED_NOT_EXECUTED,
        fund_c_status=EVIDENCE_ONLY_NOT_CONSUMED,
        reasons=reasons,
    )


class FormalOpportunityUniverseConsumer:
    """Compose the formal Topic universe without inventing downstream policy."""

    def build(
        self,
        *,
        as_of: date,
        expected_topic_ids: Sequence[str],
        topics: Iterable[FormalTopicState],
        eligibility: Iterable[FormalTopicEligibility],
        relations: Iterable[FormalTopicMemberRelation],
        prices: Iterable[FormalPriceObservation] = (),
        require_price_evidence: bool = False,
    ) -> FormalOpportunityUniverseReadModel:
        expected_ids = tuple(sorted(set(expected_topic_ids)))
        if not expected_ids:
            raise FormalOpportunityUniverseError("expected_topic_ids cannot be empty")
        if any(not isinstance(item, str) or not item.strip() for item in expected_ids):
            raise FormalOpportunityUniverseError("expected_topic_ids must contain non-empty ids")

        topic_rows = tuple(topics)
        eligibility_rows = tuple(eligibility)
        relation_rows = tuple(relations)
        price_rows = tuple(prices)
        topic_by_id: dict[str, FormalTopicState] = {}
        decision_by_id: dict[str, FormalTopicEligibility] = {}
        for row in topic_rows:
            if row.topic_id in topic_by_id:
                raise FormalOpportunityUniverseError(f"duplicate Topic state: {row.topic_id}")
            topic_by_id[row.topic_id] = row
        for row in eligibility_rows:
            if row.topic_id in decision_by_id:
                raise FormalOpportunityUniverseError(f"duplicate Topic eligibility: {row.topic_id}")
            decision_by_id[row.topic_id] = row

        expected_set = set(expected_ids)
        actual_set = set(topic_by_id)
        if actual_set != expected_set:
            missing = sorted(expected_set - actual_set)
            extra = sorted(actual_set - expected_set)
            reasons = tuple(
                item
                for item in (
                    f"MISSING_FORMAL_TOPIC_STATE:{','.join(missing)}" if missing else None,
                    f"UNEXPECTED_TOPIC_STATE:{','.join(extra)}" if extra else None,
                )
                if item is not None
            )
            return _empty_result(
                as_of=as_of,
                status=UNAVAILABLE,
                expected_topic_count=len(expected_ids),
                unavailable_topic_count=len(missing),
                unavailable_topic_ids=tuple(missing),
                reasons=reasons,
            )

        eligible_topics: list[str] = []
        ineligible_topics: list[str] = []
        unavailable_topics: list[str] = []
        hard_reasons: list[str] = []
        for topic_id in expected_ids:
            topic = topic_by_id[topic_id]
            decision = decision_by_id.get(topic_id)
            if topic.topic_type != FORMAL_TOPIC_LEVEL:
                unavailable_topics.append(topic_id)
                hard_reasons.append(f"PARENT_TOPIC_NOT_OPPORTUNITY_UNIT:{topic_id}")
                continue
            if topic.as_of != as_of:
                unavailable_topics.append(topic_id)
                hard_reasons.append(f"TOPIC_AS_OF_MISMATCH:{topic_id}")
                continue
            if topic.publication_status != FORMAL_PUBLICATION_STATUS:
                unavailable_topics.append(topic_id)
                hard_reasons.append(f"TOPIC_NOT_FORMALLY_PUBLISHED:{topic_id}")
                continue
            if topic.data_status not in {"FORMAL_PUBLISHED", "FORMAL_EMPTY"}:
                unavailable_topics.append(topic_id)
                hard_reasons.append(f"TOPIC_DATA_NOT_FORMAL:{topic_id}")
                continue
            if decision is None:
                hard_reasons.append(f"OWNER_DECISION_REQUIRED:MISSING_TOPIC_ELIGIBILITY:{topic_id}")
                continue
            if decision.as_of != as_of:
                unavailable_topics.append(topic_id)
                hard_reasons.append(f"ELIGIBILITY_AS_OF_MISMATCH:{topic_id}")
                continue
            if decision.status == OWNER_DECISION_REQUIRED:
                hard_reasons.append(f"OWNER_DECISION_REQUIRED:{topic_id}")
            elif decision.status == UNAVAILABLE:
                unavailable_topics.append(topic_id)
                hard_reasons.append(f"TOPIC_ELIGIBILITY_UNAVAILABLE:{topic_id}")
            elif decision.status == ELIGIBLE:
                eligible_topics.append(topic_id)
            elif decision.status == INELIGIBLE:
                ineligible_topics.append(topic_id)

        if any(reason.startswith("OWNER_DECISION_REQUIRED") for reason in hard_reasons):
            return _empty_result(
                as_of=as_of,
                status=OWNER_DECISION_REQUIRED,
                expected_topic_count=len(expected_ids),
                available_topic_count=len(eligible_topics) + len(ineligible_topics),
                eligible_topic_count=len(eligible_topics),
                ineligible_topic_count=len(ineligible_topics),
                unavailable_topic_count=len(unavailable_topics),
                unavailable_topic_ids=tuple(sorted(unavailable_topics)),
                reasons=tuple(sorted(hard_reasons)),
            )

        relation_groups: dict[str, list[FormalTopicMemberRelation]] = defaultdict(list)
        excluded_reasons: defaultdict[str, int] = defaultdict(int)
        hard_relation_reasons: list[str] = []
        for relation in relation_rows:
            if relation.topic_id not in eligible_topics:
                continue
            if relation.publication_status != FORMAL_PUBLICATION_STATUS:
                hard_relation_reasons.append(f"RELATION_NOT_FORMALLY_PUBLISHED:{relation.relation_id}")
                continue
            if relation.valid_from > as_of:
                excluded_reasons["FUTURE_RELATION_NOT_LOOKAHEAD"] += 1
                continue
            if relation.valid_to is not None and relation.valid_to < as_of:
                excluded_reasons["EXPIRED_RELATION"] += 1
                continue
            if relation.approval_state != APPROVED_RELATION_STATE:
                excluded_reasons["UNAPPROVED_RELATION"] += 1
                continue
            if relation.instrument_type != "EQUITY":
                excluded_reasons["NON_EQUITY"] += 1
                continue
            if relation.market_code not in _ALLOWED_MARKETS:
                excluded_reasons["MARKET_OUTSIDE_FORMAL_SCOPE"] += 1
                continue
            if relation.instrument_status != ACTIVE_INSTRUMENT_STATE:
                reason = (
                    "LIFECYCLE_EXCLUDED"
                    if relation.instrument_status in _EXCLUDED_INSTRUMENT_STATES
                    else "INSTRUMENT_NOT_ACTIVE"
                )
                excluded_reasons[reason] += 1
                continue
            relation_groups[relation.instrument_id].append(relation)

        if hard_relation_reasons:
            return _empty_result(
                as_of=as_of,
                status=UNAVAILABLE,
                expected_topic_count=len(expected_ids),
                available_topic_count=len(eligible_topics) + len(ineligible_topics),
                eligible_topic_count=len(eligible_topics),
                ineligible_topic_count=len(ineligible_topics),
                unavailable_topic_count=len(unavailable_topics),
                unavailable_topic_ids=tuple(sorted(unavailable_topics)),
                reasons=tuple(sorted(hard_reasons + hard_relation_reasons)),
                excluded_relation_count=sum(excluded_reasons.values()),
                excluded_relation_reasons=tuple(sorted(excluded_reasons.items())),
            )

        price_by_instrument: dict[str, FormalPriceObservation] = {}
        for price in price_rows:
            if price.instrument_id in price_by_instrument:
                raise FormalOpportunityUniverseError(
                    f"duplicate price observation: {price.instrument_id}"
                )
            price_by_instrument[price.instrument_id] = price

        price_boundary_status = PRICE_NOT_REQUESTED
        price_errors: list[str] = []
        if require_price_evidence and relation_groups:
            price_boundary_status = PRICE_AVAILABLE
            for instrument_id in sorted(relation_groups):
                price = price_by_instrument.get(instrument_id)
                if price is None:
                    price_errors.append(f"PRICE_MISSING:{instrument_id}")
                    continue
                if price.as_of != as_of:
                    price_errors.append(f"PRICE_AS_OF_MISMATCH:{instrument_id}")
                    continue
                if price.status != "AVAILABLE":
                    price_errors.append(f"PRICE_NOT_AVAILABLE:{instrument_id}")
            if price_errors:
                price_boundary_status = PRICE_UNAVAILABLE

        instruments: list[FormalInstrumentMember] = []
        for instrument_id in sorted(relation_groups):
            rows = sorted(
                relation_groups[instrument_id],
                key=lambda item: (item.topic_id, item.relation_id),
            )
            price_status = PRICE_NOT_REQUESTED
            if require_price_evidence:
                price_status = (
                    PRICE_AVAILABLE
                    if instrument_id in price_by_instrument
                    and price_by_instrument[instrument_id].as_of == as_of
                    and price_by_instrument[instrument_id].status == "AVAILABLE"
                    else PRICE_UNAVAILABLE
                )
            instruments.append(
                FormalInstrumentMember(
                    instrument_id=instrument_id,
                    instrument_code=rows[0].instrument_code,
                    instrument_name=rows[0].instrument_name,
                    market_code=rows[0].market_code,
                    topic_ids=tuple(sorted({item.topic_id for item in rows})),
                    topic_slugs=tuple(
                        topic_by_id[topic_id].slug
                        for topic_id in sorted({row.topic_id for row in rows})
                    ),
                    topic_names=tuple(
                        topic_by_id[topic_id].name
                        for topic_id in sorted({row.topic_id for row in rows})
                    ),
                    relation_ids=tuple(item.relation_id for item in rows),
                    relation_types=tuple(sorted({item.relation_type for item in rows})),
                    structural_roles=tuple(
                        sorted({item.structural_role for item in rows if item.structural_role})
                    ),
                    price_status=price_status,
                )
            )

        full_topic_universe = not unavailable_topics
        common_kwargs = {
            "as_of": as_of,
            "expected_topic_count": len(expected_ids),
            "available_topic_count": len(eligible_topics) + len(ineligible_topics),
            "eligible_topic_count": len(eligible_topics),
            "ineligible_topic_count": len(ineligible_topics),
            "unavailable_topic_count": len(unavailable_topics),
            "unavailable_topic_ids": tuple(sorted(unavailable_topics)),
            "member_relation_count": sum(len(rows) for rows in relation_groups.values()),
            "unique_instrument_count": len(instruments),
            "excluded_relation_count": sum(excluded_reasons.values()),
            "instruments": tuple(instruments),
            "excluded_relation_reasons": tuple(sorted(excluded_reasons.items())),
            "price_boundary_status": price_boundary_status,
        }
        reasons = tuple(sorted(hard_reasons + price_errors))
        if price_errors:
            return _empty_result(
                status=UNAVAILABLE,
                reasons=reasons,
                full_topic_universe=full_topic_universe,
                **common_kwargs,
            )
        if not full_topic_universe:
            return _empty_result(
                status=(PARTIAL if common_kwargs["available_topic_count"] else UNAVAILABLE),
                reasons=reasons or ("FULL_TOPIC_UNIVERSE_NOT_PROVEN",),
                **common_kwargs,
            )
        if not instruments:
            return _empty_result(
                status=ZERO_VALID_CANDIDATES,
                full_topic_universe=True,
                publishable=True,
                publication_status=FORMAL_PUBLICATION_STATUS,
                source_status=FORMAL_SOURCE_STATUS,
                reasons=reasons or ("NO_VALID_APPROVED_ACTIVE_MEMBERS",),
                **common_kwargs,
            )
        return _empty_result(
            status=READY,
            full_topic_universe=True,
            publishable=True,
            publication_status=FORMAL_PUBLICATION_STATUS,
            source_status=FORMAL_SOURCE_STATUS,
            reasons=reasons,
            **common_kwargs,
        )


def build_formal_opportunity_universe(
    **kwargs: Any,
) -> FormalOpportunityUniverseReadModel:
    """Convenience entry point for a future approved formal provider adapter."""

    return FormalOpportunityUniverseConsumer().build(**kwargs)


__all__ = [
    "ACTIVE_INSTRUMENT_STATE",
    "APPROVED_RELATION_STATE",
    "CONTRACT_VERSION",
    "ELIGIBLE",
    "EVIDENCE_ONLY_NOT_CONSUMED",
    "FORMAL_PUBLICATION_STATUS",
    "FORMAL_SOURCE_STATUS",
    "FORMAL_TOPIC_LEVEL",
    "INELIGIBLE",
    "NOT_RUN",
    "OWNER_DECISION_REQUIRED",
    "PARTIAL",
    "PRICE_AVAILABLE",
    "PRICE_NOT_REQUESTED",
    "PRICE_UNAVAILABLE",
    "READY",
    "UNAVAILABLE",
    "UNAVAILABLE_PUBLICATION_STATUS",
    "UNAVAILABLE_SOURCE_STATUS",
    "UNCHANGED_NOT_EXECUTED",
    "ZERO_VALID_CANDIDATES",
    "FormalInstrumentMember",
    "FormalOpportunityUniverseConsumer",
    "FormalOpportunityUniverseError",
    "FormalOpportunityUniverseReadModel",
    "FormalPriceObservation",
    "FormalTopicEligibility",
    "FormalTopicMemberRelation",
    "FormalTopicState",
    "build_formal_opportunity_universe",
]
