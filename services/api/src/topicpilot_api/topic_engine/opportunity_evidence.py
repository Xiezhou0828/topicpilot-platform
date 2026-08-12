"""Deterministic, shadow-only Opportunity evidence builders.

The builders in this module calculate *facts* from an explicit canonical daily
OHLCV sequence.  They do not rank securities, publish an Opportunity, mutate
state, or replace :mod:`opportunity_shadow`'s composer.  Every numeric rule is
carried by :class:`OpportunityEvidencePolicy`; the bundled defaults are
explicitly provisional and tunable until PM approval.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, replace
from datetime import date
from decimal import Decimal
from math import isfinite

from .opportunity_shadow import (
    EVIDENCE_DERIVED,
    EVIDENCE_OBSERVED,
    EVIDENCE_UNAVAILABLE,
    FAIL,
    PASS,
    UNKNOWN,
    WAIT,
    ChipConfirmationFacts,
    EntryQualityFacts,
    Evidence,
    OpportunityShadowInput,
    RiskGateFacts,
    StageAssessment,
    StockOpportunityContext,
    TechnicalStructureFacts,
    TopicOpportunityContext,
)

OPPORTUNITY_EVIDENCE_POLICY_VERSION = "opportunity-evidence.v1.provisional"
POLICY_STATUS_PROVISIONAL = "PROVISIONAL"
POLICY_STATUS: str = POLICY_STATUS_PROVISIONAL
CANONICAL_OHLCV_SOURCE = "CANONICAL_OHLCV"
DAILY_BAR_SEMANTICS = "DAILY_BAR"


def _finite(value: float | Decimal | int | None) -> bool:
    return value is not None and not isinstance(value, bool) and isfinite(float(value))


def _number(value: float | Decimal | int | None) -> float | None:
    return None if value is None else float(value)


def _pct(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator in (None, 0):
        return None
    return (numerator / denominator) * 100.0


@dataclass(frozen=True)
class OpportunityEvidencePolicy:
    """Versioned rule bundle; all numeric values are provisional/tunable.

    These defaults are useful for deterministic shadow fixtures only.  They
    are not production thresholds and must not be interpreted as PM-frozen
    product rules.
    """

    policy_version: str = OPPORTUNITY_EVIDENCE_POLICY_VERSION
    policy_status: str = POLICY_STATUS_PROVISIONAL
    min_ohlcv_observations: int = 60
    ma20_window: int = 20
    ma60_window: int = 60
    ma_slope_lookback: int = 5
    volume_baseline_window: int = 20
    volume_confirmation_ratio: float = 1.20
    range_position_min: float = 0.50
    breakout_lookback: int = 20
    breakout_tolerance_pct: float = 0.0
    retest_tolerance_pct: float = 2.0
    support_lookback: int = 60
    weak_candle_lookback: int = 5
    weak_candle_upper_shadow_ratio: float = 0.60
    weak_candle_min_count: int = 2
    bearish_break_tolerance_pct: float = 1.0
    abnormal_downside_pct: float = 3.0
    support_distance_pass_max_pct: float = 5.0
    support_distance_wait_max_pct: float = 8.0

    def __post_init__(self) -> None:
        if self.policy_status != POLICY_STATUS_PROVISIONAL:
            raise ValueError("Opportunity evidence policy must remain PROVISIONAL")
        positive_ints = (
            "min_ohlcv_observations",
            "ma20_window",
            "ma60_window",
            "ma_slope_lookback",
            "volume_baseline_window",
            "breakout_lookback",
            "support_lookback",
            "weak_candle_lookback",
            "weak_candle_min_count",
        )
        for name in positive_ints:
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        thresholds = (
            "volume_confirmation_ratio",
            "range_position_min",
            "breakout_tolerance_pct",
            "retest_tolerance_pct",
            "weak_candle_upper_shadow_ratio",
            "bearish_break_tolerance_pct",
            "abnormal_downside_pct",
            "support_distance_pass_max_pct",
            "support_distance_wait_max_pct",
        )
        for name in thresholds:
            value = getattr(self, name)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not isfinite(float(value))
            ):
                raise ValueError(f"{name} must be finite")
            if float(value) < 0:
                raise ValueError(f"{name} must be non-negative")
        if self.range_position_min > 1 or self.weak_candle_upper_shadow_ratio > 1:
            raise ValueError("ratio thresholds must be between 0 and 1")
        if self.support_distance_wait_max_pct < self.support_distance_pass_max_pct:
            raise ValueError("wait distance must not be below pass distance")

    def as_dict(self) -> dict[str, object]:
        numeric = {
            name: getattr(self, name)
            for name in self.__dataclass_fields__
            if name not in {"policy_version", "policy_status"}
        }
        return {
            "policyVersion": self.policy_version,
            "policyStatus": self.policy_status,
            "numericParameters": numeric,
            "numericParameterStatus": "PROVISIONAL_TUNABLE",
        }


@dataclass(frozen=True)
class CanonicalOHLCVBar:
    """One accepted canonical daily OHLCV observation.

    ``None`` is retained as missing data; it is never replaced with zero.
    ``source`` and ``observation_semantics`` make accidental use of a quote,
    frontend payload, synthetic value, or intraday row visible to callers.
    """

    trading_date: date
    open: float | Decimal | None
    high: float | Decimal | None
    low: float | Decimal | None
    close: float | Decimal | None
    volume: float | Decimal | None
    source: str = CANONICAL_OHLCV_SOURCE
    observation_semantics: str = DAILY_BAR_SEMANTICS
    quality_state: str = "ACCEPTED"
    instrument_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.trading_date, date):
            raise ValueError("trading_date must be a date")
        if (
            self.source != CANONICAL_OHLCV_SOURCE
            or self.observation_semantics != DAILY_BAR_SEMANTICS
        ):
            raise ValueError("evidence builders require canonical DAILY_BAR observations")
        if self.quality_state != "ACCEPTED":
            raise ValueError("evidence builders require accepted canonical observations")
        for name in ("open", "high", "low", "close", "volume"):
            value = getattr(self, name)
            if value is not None and not _finite(value):
                raise ValueError(f"{name} must be finite or null")
            if name == "volume" and value is not None and float(value) < 0:
                raise ValueError("volume must be non-negative")
        if all(getattr(self, name) is not None for name in ("open", "high", "low", "close")):
            if float(self.high) < max(float(self.open), float(self.close)):
                raise ValueError("high must be >= open and close")
            if float(self.low) > min(float(self.open), float(self.close)):
                raise ValueError("low must be <= open and close")


@dataclass(frozen=True)
class OHLCVSufficiencyEvidence:
    assessment: StageAssessment
    available_count: int
    required_count: int
    latest_trading_date: date | None
    missing_bar_count: int
    as_of: date | None


@dataclass(frozen=True)
class MovingAverageEvidence:
    window: int
    status: str
    value: float | None
    previous_value: float | None
    direction: str
    observations_used: int
    as_of: date | None
    evidence: tuple[Evidence, ...]


@dataclass(frozen=True)
class PriceVolumeEvidence:
    assessment: StageAssessment
    price: float | None
    previous_close: float | None
    price_change_pct: float | None
    volume: float | None
    average_volume: float | None
    relative_volume: float | None
    range_position: float | None


@dataclass(frozen=True)
class BreakoutEvidence:
    assessment: StageAssessment
    reference_price: float | None
    current_price: float | None
    distance_pct: float | None
    lookback: int
    evidence: tuple[Evidence, ...]


@dataclass(frozen=True)
class RetestEvidence:
    assessment: StageAssessment
    reference_price: float | None
    current_low: float | None
    current_close: float | None
    distance_pct: float | None
    evidence: tuple[Evidence, ...]


@dataclass(frozen=True)
class SupportCandidate:
    support_type: str
    price: float | None
    distance_pct: float | None
    strength: str
    available: bool
    evidence: tuple[Evidence, ...] = ()


@dataclass(frozen=True)
class SupportEvidence:
    assessment: StageAssessment
    candidates: tuple[SupportCandidate, ...]
    primary_support: SupportCandidate | None
    selection_reason: str


@dataclass(frozen=True)
class WeakCandleEvidence:
    assessment: StageAssessment
    weak_count: int
    lookback: int
    latest_upper_shadow_ratio: float | None
    evidence: tuple[Evidence, ...]


@dataclass(frozen=True)
class BearishBreakEvidence:
    assessment: StageAssessment
    broken_support: SupportCandidate | None
    broke_ma20: bool | None
    broke_structural_low: bool | None
    abnormal_downside: bool | None
    evidence: tuple[Evidence, ...]


@dataclass(frozen=True)
class TechnicalEvidenceBundle:
    sufficiency: OHLCVSufficiencyEvidence
    ma20: MovingAverageEvidence
    ma60: MovingAverageEvidence
    price_volume: PriceVolumeEvidence
    breakout: BreakoutEvidence
    retest: RetestEvidence
    support: SupportEvidence
    weak_candle: WeakCandleEvidence
    bearish_break: BearishBreakEvidence
    technical_facts: TechnicalStructureFacts


@dataclass(frozen=True)
class OpportunityShadowInputBuild:
    input: OpportunityShadowInput
    technical: TechnicalEvidenceBundle
    entry: EntryQualityFacts
    risk: RiskGateFacts
    policy: OpportunityEvidencePolicy


def _ordered_bars(
    bars: Iterable[CanonicalOHLCVBar], as_of: date | None
) -> tuple[CanonicalOHLCVBar, ...]:
    values = tuple(bar for bar in bars if as_of is None or bar.trading_date <= as_of)
    ordered = tuple(sorted(values, key=lambda item: item.trading_date))
    if len({bar.trading_date for bar in ordered}) != len(ordered):
        raise ValueError("canonical OHLCV bars must have unique trading dates")
    return ordered


def _close_bars(bars: Sequence[CanonicalOHLCVBar]) -> tuple[CanonicalOHLCVBar, ...]:
    return tuple(bar for bar in bars if bar.close is not None)


def build_ohlcv_sufficiency(
    bars: Iterable[CanonicalOHLCVBar],
    policy: OpportunityEvidencePolicy | None = None,
    *,
    as_of: date | None = None,
) -> OHLCVSufficiencyEvidence:
    policy = policy or OpportunityEvidencePolicy()
    ordered = _ordered_bars(bars, as_of)
    usable = tuple(bar for bar in ordered if bar.close is not None and bar.volume is not None)
    latest = ordered[-1].trading_date if ordered else None
    missing = len(ordered) - len(usable)
    status = PASS if len(usable) >= policy.min_ohlcv_observations else FAIL
    reason = "OHLCV_SUFFICIENT" if status == PASS else "OHLCV_INSUFFICIENT"
    evidence = (
        Evidence("OHLCV_AVAILABLE_COUNT", EVIDENCE_OBSERVED, len(usable)),
        Evidence("OHLCV_REQUIRED_COUNT", EVIDENCE_DERIVED, policy.min_ohlcv_observations),
        Evidence("OHLCV_MISSING_BAR_COUNT", EVIDENCE_OBSERVED, missing),
        Evidence(
            "OHLCV_LATEST_TRADING_DATE", EVIDENCE_OBSERVED, latest.isoformat() if latest else None
        ),
        Evidence("OHLCV_AS_OF", EVIDENCE_OBSERVED, as_of.isoformat() if as_of else None),
        Evidence("EVIDENCE_POLICY_STATUS", EVIDENCE_OBSERVED, policy.policy_status),
    )
    return OHLCVSufficiencyEvidence(
        StageAssessment(status, (reason,), evidence),
        len(usable),
        policy.min_ohlcv_observations,
        latest,
        missing,
        as_of,
    )


def _ma_for_window(
    bars: Sequence[CanonicalOHLCVBar],
    window: int,
    slope_lookback: int,
) -> MovingAverageEvidence:
    closes = _close_bars(bars)
    if len(closes) < window:
        evidence = (
            Evidence(f"MA{window}_AVAILABLE", EVIDENCE_UNAVAILABLE, False),
            Evidence(f"MA{window}_OBSERVATIONS", EVIDENCE_OBSERVED, len(closes)),
        )
        return MovingAverageEvidence(
            window,
            UNKNOWN,
            None,
            None,
            "UNKNOWN",
            len(closes),
            closes[-1].trading_date if closes else None,
            evidence,
        )
    values = [float(item.close) for item in closes]
    current = sum(values[-window:]) / window
    previous = None
    if len(values) >= window + slope_lookback:
        previous = sum(values[-window - slope_lookback : -slope_lookback]) / window
    direction = (
        "UNKNOWN"
        if previous is None
        else ("UP" if current > previous else "DOWN" if current < previous else "FLAT")
    )
    evidence = (
        Evidence(f"MA{window}_AVAILABLE", EVIDENCE_OBSERVED, True),
        Evidence(f"MA{window}", EVIDENCE_DERIVED, current),
        Evidence(f"MA{window}_PREVIOUS", EVIDENCE_DERIVED, previous),
        Evidence(f"MA{window}_DIRECTION", EVIDENCE_DERIVED, direction),
        Evidence(f"MA{window}_OBSERVATIONS", EVIDENCE_OBSERVED, len(closes)),
    )
    return MovingAverageEvidence(
        window, PASS, current, previous, direction, len(closes), closes[-1].trading_date, evidence
    )


def build_moving_average_evidence(
    bars: Iterable[CanonicalOHLCVBar],
    policy: OpportunityEvidencePolicy | None = None,
    *,
    as_of: date | None = None,
) -> tuple[MovingAverageEvidence, MovingAverageEvidence]:
    policy = policy or OpportunityEvidencePolicy()
    ordered = _ordered_bars(bars, as_of)
    return (
        _ma_for_window(ordered, policy.ma20_window, policy.ma_slope_lookback),
        _ma_for_window(ordered, policy.ma60_window, policy.ma_slope_lookback),
    )


def build_price_volume_evidence(
    bars: Iterable[CanonicalOHLCVBar],
    policy: OpportunityEvidencePolicy | None = None,
    *,
    as_of: date | None = None,
) -> PriceVolumeEvidence:
    policy = policy or OpportunityEvidencePolicy()
    ordered = _ordered_bars(bars, as_of)
    usable = tuple(item for item in ordered if item.close is not None and item.volume is not None)
    if len(usable) < 2:
        assessment = StageAssessment(
            UNKNOWN,
            ("PRICE_VOLUME_INSUFFICIENT",),
            (Evidence("PRICE_VOLUME", EVIDENCE_UNAVAILABLE),),
        )
        return PriceVolumeEvidence(assessment, None, None, None, None, None, None, None)
    current, previous = usable[-1], usable[-2]
    price = float(current.close)
    previous_close = float(previous.close)
    volume = float(current.volume)
    baseline_bars = usable[-policy.volume_baseline_window - 1 : -1]
    avg_volume = (
        sum(float(item.volume) for item in baseline_bars) / len(baseline_bars)
        if baseline_bars
        else None
    )
    relative = volume / avg_volume if avg_volume not in (None, 0) else None
    range_bars = usable[-policy.breakout_lookback :]
    highest = (
        max(float(item.high) for item in range_bars if item.high is not None)
        if range_bars and any(item.high is not None for item in range_bars)
        else None
    )
    lowest = (
        min(float(item.low) for item in range_bars if item.low is not None)
        if range_bars and any(item.low is not None for item in range_bars)
        else None
    )
    position = (
        (price - lowest) / (highest - lowest)
        if highest is not None and lowest is not None and highest > lowest
        else None
    )
    confirmed = (
        relative is not None
        and relative >= policy.volume_confirmation_ratio
        and position is not None
        and position >= policy.range_position_min
        and price >= previous_close
    )
    status = PASS if confirmed else UNKNOWN if relative is None or position is None else FAIL
    evidence = (
        Evidence("PRICE", EVIDENCE_OBSERVED, price),
        Evidence("PREVIOUS_CLOSE", EVIDENCE_OBSERVED, previous_close),
        Evidence(
            "PRICE_CHANGE_PCT", EVIDENCE_DERIVED, _pct(price - previous_close, previous_close)
        ),
        Evidence("VOLUME", EVIDENCE_OBSERVED, volume),
        Evidence("AVERAGE_VOLUME", EVIDENCE_DERIVED, avg_volume),
        Evidence("RELATIVE_VOLUME", EVIDENCE_DERIVED, relative),
        Evidence("RANGE_POSITION", EVIDENCE_DERIVED, position),
        Evidence("PRICE_VOLUME_POLICY_STATUS", EVIDENCE_OBSERVED, policy.policy_status),
    )
    return PriceVolumeEvidence(
        StageAssessment(
            status,
            ("PRICE_VOLUME_CONFIRMED" if status == PASS else "PRICE_VOLUME_NOT_CONFIRMED",),
            evidence,
        ),
        price,
        previous_close,
        _pct(price - previous_close, previous_close),
        volume,
        avg_volume,
        relative,
        position,
    )


def build_breakout_evidence(
    bars: Iterable[CanonicalOHLCVBar],
    policy: OpportunityEvidencePolicy | None = None,
    *,
    as_of: date | None = None,
) -> BreakoutEvidence:
    policy = policy or OpportunityEvidencePolicy()
    ordered = _ordered_bars(bars, as_of)
    if len(ordered) <= policy.breakout_lookback:
        return BreakoutEvidence(
            StageAssessment(
                UNKNOWN,
                ("BREAKOUT_INSUFFICIENT",),
                (Evidence("BREAKOUT_REFERENCE", EVIDENCE_UNAVAILABLE),),
            ),
            None,
            None,
            None,
            policy.breakout_lookback,
            (),
        )
    current = ordered[-1]
    prior = ordered[-policy.breakout_lookback - 1 : -1]
    highs = [float(item.high) for item in prior if item.high is not None]
    if current.close is None or not highs:
        return BreakoutEvidence(
            StageAssessment(
                UNKNOWN,
                ("BREAKOUT_REFERENCE_UNAVAILABLE",),
                (Evidence("BREAKOUT_REFERENCE", EVIDENCE_UNAVAILABLE),),
            ),
            max(highs) if highs else None,
            _number(current.close),
            None,
            policy.breakout_lookback,
            (),
        )
    reference = max(highs)
    distance = _pct(float(current.close) - reference, reference)
    passed = float(current.close) > reference * (1 + policy.breakout_tolerance_pct / 100)
    evidence = (
        Evidence("BREAKOUT_REFERENCE", EVIDENCE_DERIVED, reference),
        Evidence("BREAKOUT_CURRENT_PRICE", EVIDENCE_OBSERVED, float(current.close)),
        Evidence("BREAKOUT_DISTANCE_PCT", EVIDENCE_DERIVED, distance),
        Evidence("BREAKOUT_LOOKBACK", EVIDENCE_OBSERVED, policy.breakout_lookback),
    )
    return BreakoutEvidence(
        StageAssessment(
            PASS if passed else FAIL, ("BREAKOUT_CONFIRMED" if passed else "NO_BREAKOUT",), evidence
        ),
        reference,
        float(current.close),
        distance,
        policy.breakout_lookback,
        evidence,
    )


def build_retest_evidence(
    bars: Iterable[CanonicalOHLCVBar],
    breakout: BreakoutEvidence | None = None,
    policy: OpportunityEvidencePolicy | None = None,
    *,
    as_of: date | None = None,
) -> RetestEvidence:
    policy = policy or OpportunityEvidencePolicy()
    ordered = _ordered_bars(bars, as_of)
    reference = breakout.reference_price if breakout else None
    if reference is None or not ordered:
        return RetestEvidence(
            StageAssessment(
                UNKNOWN,
                ("RETEST_REFERENCE_UNAVAILABLE",),
                (Evidence("RETEST_REFERENCE", EVIDENCE_UNAVAILABLE),),
            ),
            reference,
            None,
            None,
            None,
            (),
        )
    current = ordered[-1]
    low = _number(current.low)
    close = _number(current.close)
    if low is None or close is None:
        return RetestEvidence(
            StageAssessment(
                UNKNOWN,
                ("RETEST_OHLC_UNAVAILABLE",),
                (Evidence("RETEST_CURRENT_BAR", EVIDENCE_UNAVAILABLE),),
            ),
            reference,
            low,
            close,
            None,
            (),
        )
    low_distance = abs(low - reference) / reference * 100
    held = low >= reference * (1 - policy.retest_tolerance_pct / 100) and close >= reference * (
        1 - policy.retest_tolerance_pct / 100
    )
    evidence = (
        Evidence("RETEST_REFERENCE", EVIDENCE_DERIVED, reference),
        Evidence("RETEST_CURRENT_LOW", EVIDENCE_OBSERVED, low),
        Evidence("RETEST_CURRENT_CLOSE", EVIDENCE_OBSERVED, close),
        Evidence("RETEST_DISTANCE_PCT", EVIDENCE_DERIVED, low_distance),
    )
    status = PASS if held else FAIL
    return RetestEvidence(
        StageAssessment(status, ("RETEST_HELD" if held else "RETEST_FAILED",), evidence),
        reference,
        low,
        close,
        low_distance,
        evidence,
    )


def build_support_evidence(
    bars: Iterable[CanonicalOHLCVBar],
    ma20: MovingAverageEvidence,
    ma60: MovingAverageEvidence,
    breakout: BreakoutEvidence | None = None,
    policy: OpportunityEvidencePolicy | None = None,
    *,
    as_of: date | None = None,
) -> SupportEvidence:
    policy = policy or OpportunityEvidencePolicy()
    ordered = _ordered_bars(bars, as_of)
    closes = _close_bars(ordered)
    current = _number(closes[-1].close) if closes else None
    reference_bars = ordered[-policy.support_lookback - 1 : -1]
    candidates: list[SupportCandidate] = []
    if breakout and breakout.reference_price is not None:
        candidates.append(
            SupportCandidate(
                "BREAKOUT_REFERENCE",
                breakout.reference_price,
                _pct(current - breakout.reference_price, breakout.reference_price),
                "DERIVED",
                True,
                breakout.evidence,
            )
        )
    if ma20.value is not None:
        candidates.append(
            SupportCandidate(
                "MA20",
                ma20.value,
                _pct(current - ma20.value, ma20.value),
                "DERIVED",
                True,
                ma20.evidence,
            )
        )
    if ma60.value is not None:
        candidates.append(
            SupportCandidate(
                "MA60",
                ma60.value,
                _pct(current - ma60.value, ma60.value),
                "DERIVED",
                True,
                ma60.evidence,
            )
        )
    lows = [float(item.low) for item in reference_bars if item.low is not None]
    if lows:
        low = min(lows)
        candidates.append(
            SupportCandidate(
                "STRUCTURAL_LOW",
                low,
                _pct(current - low, low),
                "DERIVED",
                True,
                (Evidence("STRUCTURAL_LOW", EVIDENCE_DERIVED, low),),
            )
        )
    valid = tuple(
        item
        for item in candidates
        if item.available
        and item.price is not None
        and current is not None
        and item.price <= current
    )
    primary = max(valid, key=lambda item: item.price) if valid else None
    if primary is not None:
        assessment = StageAssessment(
            PASS,
            ("PRIMARY_SUPPORT_SELECTED",),
            tuple(e for item in candidates for e in item.evidence),
        )
        reason = f"highest_valid_support_below_price:{primary.support_type}"
    elif candidates:
        assessment = StageAssessment(
            FAIL,
            ("NO_VALID_SUPPORT_BELOW_PRICE",),
            tuple(e for item in candidates for e in item.evidence),
        )
        reason = "all_support_candidates_above_price_or_price_unavailable"
    else:
        assessment = StageAssessment(
            UNKNOWN,
            ("SUPPORT_UNAVAILABLE",),
            (Evidence("SUPPORT_CANDIDATES", EVIDENCE_UNAVAILABLE),),
        )
        reason = "no_support_candidates_available"
    return SupportEvidence(assessment, tuple(candidates), primary, reason)


def build_weak_candle_evidence(
    bars: Iterable[CanonicalOHLCVBar],
    policy: OpportunityEvidencePolicy | None = None,
    *,
    as_of: date | None = None,
) -> WeakCandleEvidence:
    policy = policy or OpportunityEvidencePolicy()
    ordered = _ordered_bars(bars, as_of)
    recent = ordered[-policy.weak_candle_lookback :]
    ratios: list[float] = []
    weak_flags: list[bool] = []
    for bar in recent:
        if None in (bar.open, bar.high, bar.low, bar.close):
            continue
        high, low, open_, close = map(float, (bar.high, bar.low, bar.open, bar.close))
        candle_range = high - low
        if candle_range <= 0:
            continue
        upper = high - max(open_, close)
        ratio = upper / candle_range
        ratios.append(ratio)
        # A long upper shadow is only a weak-candle candidate when the body is
        # not bullish.  This intentionally conservative rule avoids treating a
        # strong bullish continuation candle as bearish risk.
        weak_flags.append(ratio >= policy.weak_candle_upper_shadow_ratio and close <= open_)
    weak_count = sum(weak_flags)
    if len(ratios) < policy.weak_candle_lookback:
        status = UNKNOWN
        reason = "WEAK_CANDLE_INSUFFICIENT"
    else:
        status = FAIL if weak_count >= policy.weak_candle_min_count else PASS
        reason = "WEAK_CANDLE_RISK" if status == FAIL else "WEAK_CANDLE_NOT_CONFIRMED"
    evidence = (
        Evidence("WEAK_CANDLE_COUNT", EVIDENCE_DERIVED, weak_count),
        Evidence("WEAK_CANDLE_LOOKBACK", EVIDENCE_OBSERVED, policy.weak_candle_lookback),
        Evidence("LATEST_UPPER_SHADOW_RATIO", EVIDENCE_DERIVED, ratios[-1] if ratios else None),
    )
    return WeakCandleEvidence(
        StageAssessment(status, (reason,), evidence),
        weak_count,
        policy.weak_candle_lookback,
        ratios[-1] if ratios else None,
        evidence,
    )


def build_bearish_break_evidence(
    bars: Iterable[CanonicalOHLCVBar],
    support: SupportEvidence,
    ma20: MovingAverageEvidence,
    policy: OpportunityEvidencePolicy | None = None,
    *,
    as_of: date | None = None,
) -> BearishBreakEvidence:
    policy = policy or OpportunityEvidencePolicy()
    ordered = _ordered_bars(bars, as_of)
    closes = _close_bars(ordered)
    if not closes:
        return BearishBreakEvidence(
            StageAssessment(
                UNKNOWN,
                ("BEARISH_BREAK_INSUFFICIENT",),
                (Evidence("BEARISH_BREAK", EVIDENCE_UNAVAILABLE),),
            ),
            None,
            None,
            None,
            None,
            (),
        )
    current = float(closes[-1].close)
    previous = float(closes[-2].close) if len(closes) >= 2 else None
    primary = support.primary_support
    broken_support = (
        primary is not None
        and primary.price is not None
        and current < primary.price * (1 - policy.bearish_break_tolerance_pct / 100)
    )
    broke_ma20 = (
        None
        if ma20.value is None
        else current < ma20.value * (1 - policy.bearish_break_tolerance_pct / 100)
    )
    structural_lows = [
        float(item.low)
        for item in ordered[-policy.support_lookback - 1 : -1]
        if item.low is not None
    ]
    structural = min(structural_lows) if structural_lows else None
    broke_structural = (
        None
        if structural is None
        else current < structural * (1 - policy.bearish_break_tolerance_pct / 100)
    )
    abnormal = (
        None
        if previous in (None, 0)
        else ((previous - current) / previous * 100) >= policy.abnormal_downside_pct
    )
    unknown = primary is None or broke_ma20 is None or broke_structural is None or abnormal is None
    is_break = bool(broken_support or broke_ma20 or broke_structural or abnormal)
    status = FAIL if is_break else UNKNOWN if unknown else PASS
    reason = (
        "BEARISH_BREAK_DETECTED"
        if status == FAIL
        else "BEARISH_BREAK_NOT_CONFIRMED"
        if status == PASS
        else "BEARISH_BREAK_INCOMPLETE"
    )
    evidence = (
        Evidence(
            "BROKEN_SUPPORT",
            EVIDENCE_DERIVED,
            bool(broken_support) if primary is not None else None,
        ),
        Evidence("BROKE_MA20", EVIDENCE_DERIVED, broke_ma20),
        Evidence("BROKE_STRUCTURAL_LOW", EVIDENCE_DERIVED, broke_structural),
        Evidence("ABNORMAL_DOWNSIDE", EVIDENCE_DERIVED, abnormal),
    )
    return BearishBreakEvidence(
        StageAssessment(status, (reason,), evidence),
        primary if broken_support else None,
        broke_ma20,
        broke_structural,
        abnormal,
        evidence,
    )


def build_entry_quality(
    price: float | None,
    support: SupportEvidence,
    policy: OpportunityEvidencePolicy | None = None,
) -> EntryQualityFacts:
    policy = policy or OpportunityEvidencePolicy()
    primary = support.primary_support
    support_price = primary.price if primary else None
    if price is None or support_price is None:
        return EntryQualityFacts(
            UNKNOWN,
            price,
            None,
            reason_codes=("ENTRY_SUPPORT_UNAVAILABLE",),
            evidence=(Evidence("ENTRY_PRICE", EVIDENCE_UNAVAILABLE, price),),
        )
    distance = (price - support_price) / support_price * 100.0
    if distance <= policy.support_distance_pass_max_pct and distance >= 0:
        status = PASS
        reason = "ENTRY_WITHIN_PROVISIONAL_SUPPORT_BAND"
    elif distance <= policy.support_distance_wait_max_pct:
        status = WAIT
        reason = "ENTRY_WAIT_FOR_RETEST_OR_BETTER_POSITION"
    else:
        status = WAIT
        reason = "ENTRY_TOO_FAR_FROM_SUPPORT"
    evidence = (
        Evidence("ENTRY_PRICE", EVIDENCE_OBSERVED, price),
        Evidence("PRIMARY_SUPPORT", EVIDENCE_DERIVED, support_price),
        Evidence("SUPPORT_DISTANCE_PCT", EVIDENCE_DERIVED, distance),
        Evidence("ENTRY_POLICY_STATUS", EVIDENCE_OBSERVED, policy.policy_status),
    )
    return EntryQualityFacts(status, price, support_price, distance, (reason,), evidence)


def build_risk_gate(
    sufficiency: OHLCVSufficiencyEvidence,
    bearish_break: BearishBreakEvidence,
    weak_candle: WeakCandleEvidence,
    ma20: MovingAverageEvidence,
) -> RiskGateFacts:
    evidence = (*bearish_break.evidence, *weak_candle.evidence)
    if sufficiency.assessment.status != PASS or ma20.status == UNKNOWN:
        return RiskGateFacts(StageAssessment(UNKNOWN, ("RISK_EVIDENCE_INCOMPLETE",), evidence))
    if bearish_break.assessment.status == FAIL:
        return RiskGateFacts(StageAssessment(FAIL, ("MAJOR_SUPPORT_OR_BEARISH_BREAK",), evidence))
    if weak_candle.assessment.status == FAIL:
        return RiskGateFacts(StageAssessment(FAIL, ("WEAK_CANDLE_RISK",), evidence))
    if bearish_break.assessment.status == UNKNOWN or weak_candle.assessment.status == UNKNOWN:
        return RiskGateFacts(StageAssessment(UNKNOWN, ("RISK_EVIDENCE_INCOMPLETE",), evidence))
    return RiskGateFacts(StageAssessment(PASS, ("RISK_GATE_CLEAR",), evidence))


def build_technical_evidence(
    bars: Iterable[CanonicalOHLCVBar],
    policy: OpportunityEvidencePolicy | None = None,
    *,
    as_of: date | None = None,
) -> TechnicalEvidenceBundle:
    policy = policy or OpportunityEvidencePolicy()
    ordered = _ordered_bars(bars, as_of)
    sufficiency = build_ohlcv_sufficiency(ordered, policy, as_of=as_of)
    ma20, ma60 = build_moving_average_evidence(ordered, policy, as_of=as_of)
    price_volume = build_price_volume_evidence(ordered, policy, as_of=as_of)
    breakout = build_breakout_evidence(ordered, policy, as_of=as_of)
    retest = build_retest_evidence(ordered, breakout, policy, as_of=as_of)
    support = build_support_evidence(ordered, ma20, ma60, breakout, policy, as_of=as_of)
    weak = build_weak_candle_evidence(ordered, policy, as_of=as_of)
    bearish = build_bearish_break_evidence(ordered, support, ma20, policy, as_of=as_of)
    technical = TechnicalStructureFacts(
        ma20.status == PASS if ma20.status != UNKNOWN else None,
        ma60.status == PASS if ma60.status != UNKNOWN else None,
        (ma20.direction == "UP") if ma20.direction != "UNKNOWN" else None,
        price_volume.assessment.status == PASS
        if price_volume.assessment.status != UNKNOWN
        else None,
        (breakout.assessment.status == PASS or retest.assessment.status == PASS)
        if breakout.assessment.status != UNKNOWN or retest.assessment.status != UNKNOWN
        else None,
        support.assessment.status == PASS if support.assessment.status != UNKNOWN else None,
        bearish.assessment.status == PASS if bearish.assessment.status != UNKNOWN else None,
        weak.assessment.status == PASS if weak.assessment.status != UNKNOWN else None,
        evidence=tuple(
            evidence
            for item in (
                sufficiency.assessment,
                ma20,
                ma60,
                price_volume.assessment,
                breakout.assessment,
                retest.assessment,
                support.assessment,
                weak.assessment,
                bearish.assessment,
            )
            for evidence in getattr(item, "evidence", ())
        ),
    )
    return TechnicalEvidenceBundle(
        sufficiency, ma20, ma60, price_volume, breakout, retest, support, weak, bearish, technical
    )


class TechnicalEvidenceBuilder:
    """Small object wrapper for callers that prefer dependency injection."""

    def __init__(self, policy: OpportunityEvidencePolicy | None = None) -> None:
        self.policy = policy or OpportunityEvidencePolicy()

    def build(
        self, bars: Iterable[CanonicalOHLCVBar], *, as_of: date | None = None
    ) -> TechnicalEvidenceBundle:
        return build_technical_evidence(bars, self.policy, as_of=as_of)


class OpportunityShadowInputBuilder:
    """Build explicit Composer input without changing production semantics."""

    def __init__(self, policy: OpportunityEvidencePolicy | None = None) -> None:
        self.policy = policy or OpportunityEvidencePolicy()

    def build(
        self,
        *,
        topic: TopicOpportunityContext,
        stock: StockOpportunityContext,
        bars: Iterable[CanonicalOHLCVBar],
        chip: ChipConfirmationFacts | None = None,
        previously_tracked_state: str | None = None,
        as_of: date | None = None,
    ) -> OpportunityShadowInputBuild:
        ordered = _ordered_bars(bars, as_of)
        technical = build_technical_evidence(ordered, self.policy, as_of=as_of)
        closes = _close_bars(ordered)
        current_price = _number(closes[-1].close) if closes else None
        stock_context = replace(
            stock,
            price=current_price,
            ma20=technical.ma20.value,
            ma60=technical.ma60.value,
            sufficient_ohlcv=technical.sufficiency.assessment.status == PASS,
        )
        entry = build_entry_quality(current_price, technical.support, self.policy)
        risk = build_risk_gate(
            technical.sufficiency, technical.bearish_break, technical.weak_candle, technical.ma20
        )
        shadow_input = OpportunityShadowInput(
            topic=topic,
            stock=stock_context,
            technical=technical.technical_facts,
            risk=risk,
            entry=entry,
            chip=chip
            or ChipConfirmationFacts(
                StageAssessment(
                    UNKNOWN,
                    ("CHIP_NOT_AVAILABLE",),
                    (Evidence("CHIP_CONFIRMATION", EVIDENCE_UNAVAILABLE),),
                )
            ),
            previously_tracked_state=previously_tracked_state,
        )
        return OpportunityShadowInputBuild(shadow_input, technical, entry, risk, self.policy)


@dataclass(frozen=True)
class OpportunityShadowReplayCase:
    instrument_id: str
    topic: TopicOpportunityContext
    stock: StockOpportunityContext
    bars: tuple[CanonicalOHLCVBar, ...]
    chip: ChipConfirmationFacts | None = None
    previously_tracked_state: str | None = None


@dataclass(frozen=True)
class HistoricalShadowReplayObservation:
    evaluation_date: date
    instrument_id: str
    result: object
    latest_input_date: date | None

    def as_dict(self) -> dict[str, object]:
        return {
            "evaluationDate": self.evaluation_date.isoformat(),
            "instrumentId": self.instrument_id,
            "latestInputDate": self.latest_input_date.isoformat()
            if self.latest_input_date
            else None,
            "result": self.result.as_dict(),
        }


@dataclass(frozen=True)
class HistoricalShadowReplayResult:
    policy: OpportunityEvidencePolicy
    observations: tuple[HistoricalShadowReplayObservation, ...]
    no_lookahead: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "policy": self.policy.as_dict(),
            "noLookahead": self.no_lookahead,
            "observations": [item.as_dict() for item in self.observations],
        }


def replay_historical_shadow(
    cases: Iterable[OpportunityShadowReplayCase],
    evaluation_dates: Iterable[date],
    policy: OpportunityEvidencePolicy | None = None,
) -> HistoricalShadowReplayResult:
    """Replay each case using only bars on or before each evaluation date."""

    policy = policy or OpportunityEvidencePolicy()
    builder = OpportunityShadowInputBuilder(policy)
    observations: list[HistoricalShadowReplayObservation] = []
    ordered_cases = tuple(sorted(tuple(cases), key=lambda item: item.instrument_id))
    no_lookahead = True
    for evaluation_date in sorted(set(evaluation_dates)):
        for case in ordered_cases:
            visible = tuple(bar for bar in case.bars if bar.trading_date <= evaluation_date)
            built = builder.build(
                topic=case.topic,
                stock=case.stock,
                bars=visible,
                chip=case.chip,
                previously_tracked_state=case.previously_tracked_state,
                as_of=evaluation_date,
            )
            latest = max((bar.trading_date for bar in visible), default=None)
            no_lookahead = no_lookahead and all(
                bar.trading_date <= evaluation_date for bar in visible
            )
            from .opportunity_shadow import build_opportunity_shadow

            result = build_opportunity_shadow(built.input)
            observations.append(
                HistoricalShadowReplayObservation(
                    evaluation_date, case.instrument_id, result, latest
                )
            )
    return HistoricalShadowReplayResult(policy, tuple(observations), no_lookahead)


# Descriptive aliases make the layer easy to discover without multiplying
# implementations.
build_ohlcv_sufficiency_evidence = build_ohlcv_sufficiency
build_ma_evidence = build_moving_average_evidence
build_entry_quality_evidence = build_entry_quality
build_risk_gate_evidence = build_risk_gate
run_historical_shadow_replay = replay_historical_shadow
historical_shadow_replay = replay_historical_shadow
CanonicalOHLCV = CanonicalOHLCVBar
OpportunityInputBuilder = OpportunityShadowInputBuilder


def build_opportunity_shadow_input(
    *,
    topic: TopicOpportunityContext,
    stock: StockOpportunityContext,
    bars: Iterable[CanonicalOHLCVBar],
    policy: OpportunityEvidencePolicy | None = None,
    chip: ChipConfirmationFacts | None = None,
    previously_tracked_state: str | None = None,
    as_of: date | None = None,
) -> OpportunityShadowInputBuild:
    """Functional alias for :class:`OpportunityShadowInputBuilder`."""

    return OpportunityShadowInputBuilder(policy).build(
        topic=topic,
        stock=stock,
        bars=bars,
        chip=chip,
        previously_tracked_state=previously_tracked_state,
        as_of=as_of,
    )

__all__ = [
    "CANONICAL_OHLCV_SOURCE",
    "DAILY_BAR_SEMANTICS",
    "OPPORTUNITY_EVIDENCE_POLICY_VERSION",
    "POLICY_STATUS",
    "POLICY_STATUS_PROVISIONAL",
    "BearishBreakEvidence",
    "BreakoutEvidence",
    "CanonicalOHLCV",
    "CanonicalOHLCVBar",
    "HistoricalShadowReplayObservation",
    "HistoricalShadowReplayResult",
    "MovingAverageEvidence",
    "OHLCVSufficiencyEvidence",
    "OpportunityEvidencePolicy",
    "OpportunityInputBuilder",
    "OpportunityShadowInputBuild",
    "OpportunityShadowInputBuilder",
    "OpportunityShadowReplayCase",
    "PriceVolumeEvidence",
    "RetestEvidence",
    "SupportCandidate",
    "SupportEvidence",
    "TechnicalEvidenceBuilder",
    "TechnicalEvidenceBundle",
    "WeakCandleEvidence",
    "build_bearish_break_evidence",
    "build_breakout_evidence",
    "build_entry_quality",
    "build_entry_quality_evidence",
    "build_ma_evidence",
    "build_moving_average_evidence",
    "build_ohlcv_sufficiency",
    "build_ohlcv_sufficiency_evidence",
    "build_opportunity_shadow_input",
    "build_price_volume_evidence",
    "build_retest_evidence",
    "build_risk_gate",
    "build_risk_gate_evidence",
    "build_support_evidence",
    "build_technical_evidence",
    "build_weak_candle_evidence",
    "historical_shadow_replay",
    "replay_historical_shadow",
    "run_historical_shadow_replay",
]
