"""Provider-neutral Opportunity shadow read service for TASK-BE-024C.

This module is deliberately persistence-free.  The fixture provider gives the
web contract a deterministic, synthetic surface while the provider protocol
leaves a seam for a future canonical production read model.  No endpoint in
this module makes a recommendation, writes a database row, or recalculates
business semantics in the browser.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import replace
from typing import Any, Protocol

from topicpilot_api.problems import ApiProblem, NotFoundProblem
from topicpilot_api.topic_engine import (
    DECISION_STATE_DEFERRED,
    DECISION_STATE_EXCLUDED,
    DECISION_STATE_SELECTED,
    DECISION_STATE_WAITING_CONFIRMATION,
    DECISION_STATE_WAITING_RETEST,
    CatchUpRankingProfile,
    OpportunityReadModel,
    build_frontend_opportunity_fixtures,
)

SHADOW_READ_CONTRACT_VERSION = "opportunity-shadow-read.v1"
PUBLICATION_STATUS = "SHADOW"
FIXTURE_DATA_STATUS = "FIXTURE/SYNTHETIC"
PARAMETER_VERSION = "opportunity-parameters.provisional.v1"
STRATEGY_TREND = "TREND_CONTINUATION"
STRATEGY_CATCH_UP = "CATCH_UP"
STRATEGY_LABEL_KEYS = {
    STRATEGY_TREND: "opportunity.strategy.trendContinuation",
    STRATEGY_CATCH_UP: "opportunity.strategy.catchUp",
}
STRATEGY_SECTION_KEYS = {
    STRATEGY_TREND: "trendContinuation",
    STRATEGY_CATCH_UP: "catchUp",
}
STRATEGY_CAPS = {STRATEGY_TREND: 3, STRATEGY_CATCH_UP: 2}
STATE_DISPLAY_KEYS = {
    DECISION_STATE_SELECTED: "OPPORTUNITY_STATE_SELECTED",
    DECISION_STATE_WAITING_RETEST: "OPPORTUNITY_STATE_WAITING_RETEST",
    DECISION_STATE_WAITING_CONFIRMATION: "OPPORTUNITY_STATE_WAITING_CONFIRMATION",
    DECISION_STATE_DEFERRED: "OPPORTUNITY_STATE_DEFERRED",
    DECISION_STATE_EXCLUDED: "OPPORTUNITY_STATE_EXCLUDED",
}
RANKING_PROFILE_VERSIONS = {
    STRATEGY_TREND: "trend-continuation-ranking.v1.provisional",
    STRATEGY_CATCH_UP: CatchUpRankingProfile().profile_version,
}
READ_STATES = (
    DECISION_STATE_SELECTED,
    DECISION_STATE_WAITING_RETEST,
    DECISION_STATE_WAITING_CONFIRMATION,
    DECISION_STATE_DEFERRED,
    DECISION_STATE_EXCLUDED,
)


class ShadowProviderUnavailable(RuntimeError):
    """Raised by a provider when no approved read source is configured."""


class OpportunityReadProvider(Protocol):
    """Read-only provider interface consumed by :class:`OpportunityShadowReadService`."""

    @property
    def publication_status(self) -> str: ...

    @property
    def data_status(self) -> str: ...

    def read_models(self) -> tuple[OpportunityReadModel, ...]: ...

    def topic_catalog(self) -> Mapping[str, dict[str, Any]]: ...

    def instrument_catalog(self) -> Mapping[str, dict[str, Any]]: ...


def _fixture_with_identity(
    item: OpportunityReadModel,
    *,
    index: int,
    topic_id: str,
    topic_name: str,
    grade: str | None,
    lifecycle: str | None,
    state: str | None = None,
    strategy_id: str | None = None,
    strategy_type: str | None = None,
    instrument_id: str | None = None,
    symbol: str | None = None,
    qualification_class: str | None = None,
    qualification_status: str | None = None,
    qualification_reasons: tuple[str, ...] | None = None,
    qualification_exception: bool | None = None,
) -> OpportunityReadModel:
    """Copy a contract fixture while changing only deterministic identity/context."""

    effective_state = state or item.opportunity_state
    effective_class = qualification_class or item.qualification_class
    effective_status = qualification_status or item.qualification_status
    if (
        effective_class == "NOT_QUALIFIED"
        and grade in {"S", "A"}
        and effective_state not in {DECISION_STATE_DEFERRED, DECISION_STATE_EXCLUDED}
    ):
        effective_class = "FORMAL_OPPORTUNITY"
        effective_status = "QUALIFIED"
    return replace(
        item,
        instrument_id=instrument_id or f"fixture-{index}",
        symbol=symbol or f"FP{index:02d}",
        instrument_name=f"Fixture {index}",
        strategy_id=strategy_id or item.strategy_id,
        strategy_type=strategy_type or item.strategy_type,
        topic_id=topic_id,
        topic_name=topic_name,
        opportunity_state=effective_state,
        topic_grade=grade,
        topic_lifecycle=lifecycle,
        topic_strength=70.0 - index,
        qualification_class=effective_class,
        qualification_status=effective_status,
        qualification_reason_codes=(
            qualification_reasons
            if qualification_reasons is not None
            else item.qualification_reason_codes
        ),
        qualification_exception=(
            qualification_exception
            if qualification_exception is not None
            else item.qualification_exception
        ),
        qualification_policy_version=item.qualification_policy_version
        or "topic-opportunity-qualification.v1.provisional",
        qualification_parameter_version=item.qualification_parameter_version or PARAMETER_VERSION,
    )


def _fixture_with_strategy_and_state(
    item: OpportunityReadModel,
    *,
    strategy_id: str,
    index: int,
    state: str,
    topic_id: str,
    topic_name: str,
    grade: str | None = "A",
    lifecycle: str | None = "MAIN_RISE",
    instrument_id: str | None = None,
    symbol: str | None = None,
    qualification_class: str | None = None,
    qualification_status: str | None = None,
    qualification_reasons: tuple[str, ...] | None = None,
    qualification_exception: bool | None = None,
) -> OpportunityReadModel:
    """Create a fixture with internally consistent strategy/state explanation."""

    explanation = replace(
        item.explanation,
        strategy=strategy_id,
        state=state,
        summary_code=STATE_DISPLAY_KEYS[state],
    )
    return replace(
        _fixture_with_identity(
            item,
            index=index,
            topic_id=topic_id,
            topic_name=topic_name,
            grade=grade,
            lifecycle=lifecycle,
            state=state,
            strategy_id=strategy_id,
            strategy_type=strategy_id,
            instrument_id=instrument_id,
            symbol=symbol,
            qualification_class=qualification_class,
            qualification_status=qualification_status,
            qualification_reasons=qualification_reasons,
            qualification_exception=qualification_exception,
        ),
        explanation=explanation,
    )


class FixtureOpportunityReadProvider:
    """Deterministic synthetic provider; it never touches the production DB."""

    publication_status = PUBLICATION_STATUS
    data_status = FIXTURE_DATA_STATUS

    def __init__(self, fixtures: Iterable[OpportunityReadModel] | None = None) -> None:
        base = tuple(fixtures or build_frontend_opportunity_fixtures())
        if len(base) < 6:
            raise ValueError("shadow fixtures must cover all decision states")
        # Keep the legacy six-state fixture history and add explicit five-state
        # Trend/Catch-up coverage, B-exception/Mature cases, and shared-stock
        # multi-topic cases required by the 024C projections.
        extras = (
            _fixture_with_strategy_and_state(
                base[0],
                strategy_id=STRATEGY_TREND,
                index=7,
                state=DECISION_STATE_SELECTED,
                topic_id="topic-warming",
                topic_name="Warming Topic",
                grade="B",
                lifecycle="FERMENTING",
                qualification_class="EXCEPTION_CANDIDATE",
                qualification_status="EXCEPTION_CANDIDATE",
                qualification_reasons=(
                    "TOPIC_GRADE_B_EXCEPTION_CANDIDATE",
                    "TOPIC_WARMING_SIGNAL",
                ),
                qualification_exception=True,
            ),
            _fixture_with_identity(
                base[1],
                index=8,
                topic_id="topic-mature",
                topic_name="Mature Topic",
                grade="A",
                lifecycle="MATURE",
            ),
            _fixture_with_strategy_and_state(
                base[4],
                strategy_id=STRATEGY_TREND,
                index=9,
                state=DECISION_STATE_EXCLUDED,
                topic_id="topic-declining",
                topic_name="Declining Topic",
                grade="D",
                lifecycle="DECLINING",
                qualification_class="NOT_QUALIFIED",
                qualification_status="EXCLUDED",
                qualification_reasons=("TOPIC_GRADE_D_HARD_EXCLUDE",),
                qualification_exception=False,
            ),
            _fixture_with_strategy_and_state(
                base[3],
                strategy_id=STRATEGY_TREND,
                index=10,
                state=DECISION_STATE_WAITING_CONFIRMATION,
                topic_id="topic-trend-confirmation",
                topic_name="Trend Confirmation Topic",
                lifecycle="SPROUTING",
            ),
            _fixture_with_strategy_and_state(
                base[5],
                strategy_id=STRATEGY_TREND,
                index=11,
                state=DECISION_STATE_DEFERRED,
                topic_id="topic-trend-deferred",
                topic_name="Trend Deferred Topic",
                grade=None,
                lifecycle=None,
            ),
            _fixture_with_strategy_and_state(
                base[1],
                strategy_id=STRATEGY_CATCH_UP,
                index=12,
                state=DECISION_STATE_WAITING_RETEST,
                topic_id="topic-catchup-retest",
                topic_name="Catch-up Retest Topic",
            ),
            _fixture_with_strategy_and_state(
                base[4],
                strategy_id=STRATEGY_CATCH_UP,
                index=13,
                state=DECISION_STATE_EXCLUDED,
                topic_id="topic-catchup-excluded",
                topic_name="Catch-up Excluded Topic",
                grade="D",
                lifecycle="DECLINING",
                qualification_class="NOT_QUALIFIED",
                qualification_status="EXCLUDED",
                qualification_reasons=("TOPIC_GRADE_D_HARD_EXCLUDE",),
                qualification_exception=False,
            ),
            _fixture_with_strategy_and_state(
                base[0],
                strategy_id=STRATEGY_TREND,
                index=14,
                state=DECISION_STATE_SELECTED,
                topic_id="topic-shared-a",
                topic_name="Shared Topic A",
                instrument_id="fixture-shared",
                symbol="SH01",
            ),
            _fixture_with_strategy_and_state(
                base[2],
                strategy_id=STRATEGY_CATCH_UP,
                index=15,
                state=DECISION_STATE_SELECTED,
                topic_id="topic-shared-b",
                topic_name="Shared Topic B",
                instrument_id="fixture-shared",
                symbol="SH01",
            ),
        )
        self._fixtures = tuple(base) + extras
        self._topic_catalog = {item.topic_id: _topic_payload(item) for item in self._fixtures}
        self._topic_catalog["topic-empty"] = {
            "id": "topic-empty",
            "name": "Empty Topic",
            "grade": "S",
            "lifecycle": "MAIN_RISE",
            "strength": None,
        }
        self._instrument_catalog = {
            item.instrument_id: _instrument_payload(item) for item in self._fixtures
        }
        self._instrument_catalog["fixture-empty-stock"] = {
            "id": "fixture-empty-stock",
            "symbol": "EMPTY",
            "name": "Empty Stock",
        }

    def read_models(self) -> tuple[OpportunityReadModel, ...]:
        return self._fixtures

    def topic_catalog(self) -> Mapping[str, dict[str, Any]]:
        return self._topic_catalog

    def instrument_catalog(self) -> Mapping[str, dict[str, Any]]:
        return self._instrument_catalog


class CanonicalOpportunityReadProvider:
    """Placeholder for the future canonical production read-model adapter."""

    publication_status = PUBLICATION_STATUS
    data_status = "UNAVAILABLE"

    def read_models(self) -> tuple[OpportunityReadModel, ...]:
        raise ShadowProviderUnavailable(
            "No canonical production Opportunity read provider is configured."
        )

    def topic_catalog(self) -> Mapping[str, dict[str, Any]]:
        return {}

    def instrument_catalog(self) -> Mapping[str, dict[str, Any]]:
        return {}


def _opportunity_id(item: OpportunityReadModel) -> str:
    as_of = item.as_of.isoformat() if item.as_of else "unknown-date"
    return ":".join(
        (
            "shadow",
            item.strategy_id.lower(),
            item.topic_id,
            item.instrument_id,
            as_of,
            item.opportunity_state.lower(),
        )
    )


def _ranked(items: Iterable[OpportunityReadModel]) -> list[OpportunityReadModel]:
    return sorted(
        items,
        key=lambda item: (
            item.rank_score is not None,
            item.rank_score if item.rank_score is not None else float("-inf"),
            item.instrument_id,
        ),
        reverse=True,
    )


def _topic_payload(item: OpportunityReadModel) -> dict[str, Any]:
    return {
        "id": item.topic_id,
        "name": item.topic_name,
        "grade": item.topic_grade,
        "lifecycle": item.topic_lifecycle,
        "strength": item.topic_strength,
    }


def _instrument_payload(item: OpportunityReadModel) -> dict[str, Any]:
    return {"id": item.instrument_id, "symbol": item.symbol, "name": item.instrument_name}


def _card(item: OpportunityReadModel, rank: int) -> dict[str, Any]:
    explanation = item.explanation.as_dict()
    opportunity_id = _opportunity_id(item)
    topic = _topic_payload(item)
    instrument = _instrument_payload(item)
    reason_codes = tuple(dict.fromkeys(item.qualification_reason_codes + item.exclusion_codes))
    data_quality = tuple(explanation.get("dataQuality", ()))
    missing_evidence = tuple(
        factor.get("code")
        for factor in data_quality
        if factor.get("status") == "UNKNOWN" and factor.get("code")
    )
    return {
        "opportunityId": opportunity_id,
        "opportunityKey": opportunity_id,
        "strategyId": item.strategy_id,
        "strategyType": item.strategy_type,
        "strategyLabelKey": STRATEGY_LABEL_KEYS.get(item.strategy_id, item.strategy_id),
        "displayKey": STATE_DISPLAY_KEYS[item.opportunity_state],
        "labelKey": STRATEGY_LABEL_KEYS.get(item.strategy_id, item.strategy_id),
        "displayOrder": rank,
        "rank": rank,
        "rankScore": item.rank_score,
        "rankingStatus": item.ranking_status,
        "instrument": instrument,
        "topic": topic,
        "instrumentId": item.instrument_id,
        "symbol": item.symbol,
        "name": item.instrument_name,
        "topicId": item.topic_id,
        "topicName": item.topic_name,
        "topicGrade": item.topic_grade,
        "topicLifecycle": item.topic_lifecycle,
        "topicStrength": item.topic_strength,
        "opportunityState": item.opportunity_state,
        "eligibility": item.eligibility,
        "status": item.status,
        "qualification": {
            "class": item.qualification_class,
            "status": item.qualification_status,
            "reasonCodes": list(item.qualification_reason_codes),
            "exceptionCandidate": item.qualification_exception,
            "policyVersion": item.qualification_policy_version,
            "parameterVersion": item.qualification_parameter_version,
        },
        "qualificationClass": item.qualification_class,
        "qualificationStatus": item.qualification_status,
        "qualificationProvenance": {
            "qualificationStatus": item.qualification_status,
            "reasonCodes": list(item.qualification_reason_codes),
            "exceptionCandidate": item.qualification_exception,
            "policyVersion": item.qualification_policy_version,
            "parameterVersion": item.qualification_parameter_version,
        },
        "confidence": item.confidence,
        "confidenceBasis": list(item.confidence_basis),
        "entryContext": [factor.as_dict() for factor in item.entry_context],
        "supportContext": [factor.as_dict() for factor in item.support_context],
        "riskContext": [factor.as_dict() for factor in item.risk_context],
        "positiveFactors": explanation["positiveFactors"],
        "waitingFactors": explanation["waitingFactors"],
        "riskFactors": explanation["riskFactors"],
        "exclusionFactors": explanation["exclusionFactors"],
        "exclusionCodes": list(item.exclusion_codes),
        "reasonCodes": list(reason_codes),
        "explanation": explanation,
        "policyVersion": item.policy_version,
        "parameterVersion": item.qualification_parameter_version or PARAMETER_VERSION,
        "rankingProfileVersion": RANKING_PROFILE_VERSIONS.get(item.strategy_id),
        "asOf": item.as_of,
        "publicationStatus": PUBLICATION_STATUS,
        "dataStatus": FIXTURE_DATA_STATUS,
        "sourceDataStatus": item.data_status,
        "evidenceCoverage": {
            "dataStatus": item.data_status,
            "factorCount": len(data_quality),
            "missingEvidence": list(missing_evidence),
        },
        "missingEvidence": list(missing_evidence),
    }


def _strategy_section(
    strategy_id: str, items: Iterable[OpportunityReadModel], *, cap: int | None = None
) -> dict[str, Any]:
    ranked = _ranked(items)
    presentation_cap = cap if cap is not None else STRATEGY_CAPS.get(strategy_id)
    presented = ranked[:presentation_cap] if presentation_cap else ranked
    cards = [_card(item, rank) for rank, item in enumerate(presented, start=1)]
    backend_ranking = [
        {
            "opportunityId": _opportunity_id(item),
            "rank": rank,
            "rankScore": item.rank_score,
            "rankingStatus": item.ranking_status,
            "opportunityState": item.opportunity_state,
        }
        for rank, item in enumerate(ranked, start=1)
    ]
    return {
        "strategyId": strategy_id,
        "strategyType": strategy_id,
        "strategyLabelKey": STRATEGY_LABEL_KEYS.get(strategy_id, strategy_id),
        "fit": "AVAILABLE" if ranked else "UNAVAILABLE",
        "candidateCount": len(ranked),
        "backendCandidateCount": len(ranked),
        "presentedCount": len(cards),
        "presentationCap": presentation_cap,
        "fullRankingRetained": True,
        "backendRanking": backend_ranking,
        "opportunities": cards,
    }


def _topic_projections(items: Iterable[OpportunityReadModel]) -> list[dict[str, Any]]:
    grouped: dict[str, list[OpportunityReadModel]] = {}
    for item in items:
        grouped.setdefault(item.topic_id, []).append(item)
    projections: list[dict[str, Any]] = []
    for topic_id in sorted(grouped):
        values = grouped[topic_id]
        sections = {
            STRATEGY_SECTION_KEYS[strategy_id]: _strategy_section(
                strategy_id,
                (item for item in values if item.strategy_id == strategy_id),
            )
            for strategy_id in (STRATEGY_TREND, STRATEGY_CATCH_UP)
        }
        projections.append(
            {
                **_topic_payload(values[0]),
                "topicId": topic_id,
                "topicName": values[0].topic_name,
                "topicGrade": values[0].topic_grade,
                "topicLifecycle": values[0].topic_lifecycle,
                "topicStrength": values[0].topic_strength,
                "asOf": values[0].as_of,
                "publicationStatus": PUBLICATION_STATUS,
                "dataStatus": FIXTURE_DATA_STATUS,
                "strategies": sections,
            }
        )
    return projections


class OpportunityShadowReadService:
    """Build topic, stock, list, and detail projections from a read provider."""

    def __init__(self, provider: OpportunityReadProvider | None = None) -> None:
        self.provider = provider or FixtureOpportunityReadProvider()
        publication_status = getattr(self.provider, "publication_status", PUBLICATION_STATUS)
        if publication_status != PUBLICATION_STATUS:
            raise ValueError("shadow read provider must publish SHADOW only")

    def _models(self) -> tuple[OpportunityReadModel, ...]:
        try:
            return self.provider.read_models()
        except ShadowProviderUnavailable as exc:
            raise ApiProblem(
                503,
                "Opportunity shadow read unavailable",
                str(exc),
                "https://topicpilot.example/problems/opportunity-shadow-unavailable",
            ) from exc

    def _topic_catalog(self) -> Mapping[str, dict[str, Any]]:
        catalog = getattr(self.provider, "topic_catalog", None)
        return catalog() if callable(catalog) else {}

    def _instrument_catalog(self) -> Mapping[str, dict[str, Any]]:
        catalog = getattr(self.provider, "instrument_catalog", None)
        return catalog() if callable(catalog) else {}

    @staticmethod
    def _filter(
        items: Iterable[OpportunityReadModel],
        *,
        strategy: str | None = None,
        state: str | None = None,
        topic_id: str | None = None,
        instrument_id: str | None = None,
        grade: str | None = None,
        lifecycle: str | None = None,
    ) -> list[OpportunityReadModel]:
        normalized_strategy = strategy.upper() if strategy else None
        normalized_state = state.upper() if state else None
        normalized_grade = grade.upper() if grade else None
        normalized_lifecycle = lifecycle.upper() if lifecycle else None
        return [
            item
            for item in items
            if (normalized_strategy is None or item.strategy_id == normalized_strategy)
            and (normalized_state is None or item.opportunity_state == normalized_state)
            and (topic_id is None or item.topic_id == topic_id)
            and (instrument_id is None or item.instrument_id == instrument_id)
            and (normalized_grade is None or item.topic_grade == normalized_grade)
            and (normalized_lifecycle is None or item.topic_lifecycle == normalized_lifecycle)
        ]

    @staticmethod
    def _status(items: Iterable[OpportunityReadModel]) -> str:
        values = tuple(items)
        if not values:
            return "EMPTY"
        if all(item.opportunity_state == DECISION_STATE_DEFERRED for item in values):
            return "DEFERRED"
        return "READY"

    def _envelope(
        self,
        *,
        items: Iterable[OpportunityReadModel],
        query: Mapping[str, Any],
        topic: dict[str, Any] | None = None,
        stock: dict[str, Any] | None = None,
        topics: list[dict[str, Any]] | None = None,
        strategies: dict[str, Any] | None = None,
        opportunities: list[dict[str, Any]] | None = None,
        opportunity: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        values = tuple(items)
        topic_value = topic
        return {
            "contractVersion": SHADOW_READ_CONTRACT_VERSION,
            "status": self._status(values),
            "publicationStatus": PUBLICATION_STATUS,
            "dataStatus": self.provider.data_status,
            "asOf": values[0].as_of if values else None,
            "query": dict(query),
            "topic": topic_value,
            "topicId": topic_value.get("id") if topic_value else None,
            "topicName": topic_value.get("name") if topic_value else None,
            "topicGrade": topic_value.get("grade") if topic_value else None,
            "topicLifecycle": topic_value.get("lifecycle") if topic_value else None,
            "topicStrength": topic_value.get("strength") if topic_value else None,
            "stock": stock,
            "topics": topics or [],
            "strategies": strategies or {},
            "opportunities": opportunities or [],
            "opportunity": opportunity,
        }

    def list_opportunities(self, **filters: Any) -> dict[str, Any]:
        limit = int(filters.pop("limit", 50))
        page = int(filters.pop("page", 1))
        cursor = filters.pop("cursor", None)
        if limit < 1 or limit > 100:
            raise ValueError("limit must be between 1 and 100")
        if page < 1:
            raise ValueError("page must be positive")
        values = self._filter(self._models(), **filters)
        sections = {
            STRATEGY_SECTION_KEYS[strategy_id]: _strategy_section(
                strategy_id,
                (item for item in values if item.strategy_id == strategy_id),
            )
            for strategy_id in (STRATEGY_TREND, STRATEGY_CATCH_UP)
        }
        presented = [card for section in sections.values() for card in section["opportunities"]]
        start = int(cursor) if cursor is not None and str(cursor).isdigit() else (page - 1) * limit
        presented = presented[start : start + limit]
        return self._envelope(
            items=values,
            query={**filters, "limit": limit, "page": page, "cursor": cursor},
            topics=_topic_projections(values),
            strategies=sections,
            opportunities=presented,
        )

    def topic_opportunities(self, topic_id: str, **filters: Any) -> dict[str, Any]:
        limit = int(filters.pop("limit", 50))
        page = int(filters.pop("page", 1))
        cursor = filters.pop("cursor", None)
        values = self._filter(self._models(), topic_id=topic_id, **filters)
        if not values:
            catalog_topic = self._topic_catalog().get(topic_id)
            if catalog_topic is not None:
                sections = {
                    STRATEGY_SECTION_KEYS[strategy_id]: _strategy_section(strategy_id, ())
                    for strategy_id in (STRATEGY_TREND, STRATEGY_CATCH_UP)
                }
                return self._envelope(
                    items=(),
                    query={
                        "topicId": topic_id,
                        **filters,
                        "limit": limit,
                        "page": page,
                        "cursor": cursor,
                    },
                    topic=catalog_topic,
                    strategies=sections,
                )
            raise NotFoundProblem(f"Topic {topic_id!r} has no shadow opportunities")
        sections = {
            STRATEGY_SECTION_KEYS[strategy_id]: _strategy_section(
                strategy_id,
                (item for item in values if item.strategy_id == strategy_id),
            )
            for strategy_id in (STRATEGY_TREND, STRATEGY_CATCH_UP)
        }
        presented = [card for section in sections.values() for card in section["opportunities"]]
        start = int(cursor) if cursor is not None and str(cursor).isdigit() else (page - 1) * limit
        return self._envelope(
            items=values,
            query={"topicId": topic_id, **filters, "limit": limit, "page": page, "cursor": cursor},
            topic=_topic_payload(values[0]),
            strategies=sections,
            opportunities=presented[start : start + limit],
        )

    def stock_opportunities(self, instrument_id: str, **filters: Any) -> dict[str, Any]:
        limit = int(filters.pop("limit", 50))
        page = int(filters.pop("page", 1))
        cursor = filters.pop("cursor", None)
        values = self._filter(self._models(), instrument_id=instrument_id, **filters)
        if not values:
            catalog_instrument = self._instrument_catalog().get(instrument_id)
            if catalog_instrument is not None:
                sections = {
                    STRATEGY_SECTION_KEYS[strategy_id]: _strategy_section(strategy_id, ())
                    for strategy_id in (STRATEGY_TREND, STRATEGY_CATCH_UP)
                }
                return self._envelope(
                    items=(),
                    query={
                        "instrumentId": instrument_id,
                        **filters,
                        "limit": limit,
                        "page": page,
                        "cursor": cursor,
                    },
                    stock=catalog_instrument,
                    strategies=sections,
                )
            raise NotFoundProblem(f"Instrument {instrument_id!r} has no shadow opportunities")
        sections = {
            STRATEGY_SECTION_KEYS[strategy_id]: _strategy_section(
                strategy_id,
                (item for item in values if item.strategy_id == strategy_id),
            )
            for strategy_id in (STRATEGY_TREND, STRATEGY_CATCH_UP)
        }
        presented = [card for section in sections.values() for card in section["opportunities"]]
        start = int(cursor) if cursor is not None and str(cursor).isdigit() else (page - 1) * limit
        return self._envelope(
            items=values,
            query={
                "instrumentId": instrument_id,
                **filters,
                "limit": limit,
                "page": page,
                "cursor": cursor,
            },
            stock=_instrument_payload(values[0]),
            strategies=sections,
            opportunities=presented[start : start + limit],
        )

    def detail(self, opportunity_id: str) -> dict[str, Any]:
        for item in self._models():
            if _opportunity_id(item) == opportunity_id:
                card = _card(item, 1)
                card["detail"] = {
                    "identity": {
                        "instrument": _instrument_payload(item),
                        "topic": _topic_payload(item),
                        "strategyId": item.strategy_id,
                    },
                    "topicContext": _topic_payload(item),
                    "qualification": card["qualification"],
                    "whyIncluded": card["positiveFactors"],
                    "waitingFor": card["waitingFactors"],
                    "risks": card["riskFactors"],
                    "entryContext": card["entryContext"],
                    "invalidationContext": card["explanation"].get("invalidationContext", []),
                    "dataConfidence": {
                        "confidence": card["confidence"],
                        "confidenceBasis": card["confidenceBasis"],
                        "evidenceCoverage": card["evidenceCoverage"],
                        "missingEvidence": card["missingEvidence"],
                        "dataQuality": card["explanation"].get("dataQuality", []),
                    },
                    "qualificationProvenance": card["qualificationProvenance"],
                    "versions": {
                        "policyVersion": card["policyVersion"],
                        "parameterVersion": card["parameterVersion"],
                        "rankingProfileVersion": card["rankingProfileVersion"],
                    },
                }
                return self._envelope(
                    items=(item,),
                    query={"opportunityId": opportunity_id},
                    topic=_topic_payload(item),
                    stock=_instrument_payload(item),
                    opportunity=card,
                )
        raise NotFoundProblem(f"Opportunity {opportunity_id!r} was not found")


_DEFAULT_SERVICE = OpportunityShadowReadService()


def get_shadow_read_service() -> OpportunityShadowReadService:
    return _DEFAULT_SERVICE


__all__ = [
    "FIXTURE_DATA_STATUS",
    "PUBLICATION_STATUS",
    "SHADOW_READ_CONTRACT_VERSION",
    "CanonicalOpportunityReadProvider",
    "FixtureOpportunityReadProvider",
    "OpportunityReadProvider",
    "OpportunityShadowReadService",
    "get_shadow_read_service",
]
