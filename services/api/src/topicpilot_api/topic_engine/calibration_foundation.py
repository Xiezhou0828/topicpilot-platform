"""Fail-closed data-foundation primitives for historical Topic calibration.

The module intentionally stays outside the runtime scoring path.  It reads
versioned authority artifacts and official market-index payloads, then emits
bounded calibration facts with explicit lineage.  It never writes authority
tables, applies migrations, or substitutes current authority for a historical
date.
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from ..structural_role_authority import load_artifact

CALIBRATION_FOUNDATION_VERSION = "topic-strength-calibration-foundation.v1"
PIT_AUTHORITY_SCHEMA_VERSION = "topic-strength-pit-authority-resolution.v1"
BENCHMARK_EXPORT_SCHEMA_VERSION = "topic-strength-official-benchmark-history.v1"

ROLE_VALUES = frozenset({"REPRESENTATIVE", "CORE", "RELATED"})
APPROVED = "APPROVED"


class CalibrationFoundationError(ValueError):
    """Raised when a source cannot be used without inventing historical facts."""


def canonical_hash(value: object) -> str:
    """Hash a JSON-compatible object using stable serialization."""

    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _date(value: object, field: str) -> date:
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError) as exc:
        raise CalibrationFoundationError(f"INVALID_DATE:{field}") from exc


def _decimal(value: object, field: str) -> Decimal:
    if value is None or isinstance(value, bool) or str(value).strip() == "":
        raise CalibrationFoundationError(f"MISSING_NUMBER:{field}")
    try:
        result = Decimal(str(value).strip().replace(",", ""))
    except (InvalidOperation, ValueError) as exc:
        raise CalibrationFoundationError(f"INVALID_NUMBER:{field}") from exc
    if not result.is_finite():
        raise CalibrationFoundationError(f"INVALID_NUMBER:{field}")
    return result


def _exchange_date(value: object) -> date:
    raw = str(value or "").strip().replace("/", "").replace("-", "")
    if len(raw) == 7 and raw.isdigit():
        return date(int(raw[:3]) + 1911, int(raw[3:5]), int(raw[5:]))
    if len(raw) == 8 and raw.isdigit():
        return date(int(raw[:4]), int(raw[4:6]), int(raw[6:]))
    raise CalibrationFoundationError("INVALID_SOURCE_DATE")


@dataclass(frozen=True)
class PITAuthorityRow:
    """One formal membership/role fact from an effective-dated artifact."""

    authority_id: str
    topic_id: str
    instrument_code: str
    market: str
    relation_type: str
    structural_role: str
    approval_state: str
    effective_from: date
    effective_to: date | None
    authority_version: str
    source_artifact_id: str
    source_artifact_hash: str
    approval_reference: str
    supersedes_authority_id: str | None
    superseded_by_authority_id: str | None
    reconstruction_status: str
    lineage: str

    def identity(self) -> tuple[str, str, str]:
        return (self.topic_id, self.market, self.instrument_code)

    def effective(self, as_of: date) -> bool:
        return self.effective_from <= as_of and (
            self.effective_to is None or as_of <= self.effective_to
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "authority_id": self.authority_id,
            "topic_id": self.topic_id,
            "instrument_code": self.instrument_code,
            "market": self.market,
            "relation_type": self.relation_type,
            "structural_role": self.structural_role,
            "approval_state": self.approval_state,
            "effective_from": self.effective_from.isoformat(),
            "effective_to": self.effective_to.isoformat() if self.effective_to else None,
            "authority_version": self.authority_version,
            "source_artifact_id": self.source_artifact_id,
            "source_artifact_hash": self.source_artifact_hash,
            "approval_reference": self.approval_reference,
            "supersedes_authority_id": self.supersedes_authority_id,
            "superseded_by_authority_id": self.superseded_by_authority_id,
            "reconstruction_status": self.reconstruction_status,
            "lineage": self.lineage,
        }


def load_pit_authority(path: Any) -> tuple[PITAuthorityRow, ...]:
    """Load the committed formal role artifact without applying it anywhere."""

    try:
        artifact = load_artifact(path)
    except Exception as exc:  # normalize source errors at this boundary
        raise CalibrationFoundationError(f"PIT_AUTHORITY_ARTIFACT_INVALID:{path}") from exc

    rows: list[PITAuthorityRow] = []
    seen: set[tuple[str, str, str]] = set()
    for raw in artifact.rows:
        try:
            role = str(raw["structuralRole"])
            approval = str(raw["approvalState"])
            market = str(raw["marketCode"])
            instrument_code = str(raw["instrumentCode"])
            topic_id = str(raw["topicId"])
            authority_id = str(raw["relationId"])
            relation_type = str(raw["relationType"])
        except (KeyError, TypeError) as exc:
            raise CalibrationFoundationError("PIT_AUTHORITY_ROW_INCOMPLETE") from exc
        if role not in ROLE_VALUES or approval != APPROVED:
            raise CalibrationFoundationError("PIT_AUTHORITY_ROW_NOT_FORMAL")
        identity = (topic_id, market, instrument_code)
        if identity in seen:
            raise CalibrationFoundationError("PIT_AUTHORITY_DUPLICATE_IDENTITY")
        seen.add(identity)
        rows.append(
            PITAuthorityRow(
                authority_id=authority_id,
                topic_id=topic_id,
                instrument_code=instrument_code,
                market=market,
                relation_type=relation_type,
                structural_role=role,
                approval_state=approval,
                effective_from=artifact.effective_date,
                effective_to=None,
                authority_version=artifact.authority_version,
                source_artifact_id=(
                    f"structural-role-authority:{artifact.authority_version}"
                ),
                source_artifact_hash=artifact.artifact_sha256,
                approval_reference=artifact.approval_reference,
                supersedes_authority_id=None,
                superseded_by_authority_id=None,
                reconstruction_status="DIRECT_FORMAL_ARTIFACT",
                lineage=(
                    f"{path}#rows[relationId={authority_id}]"
                ),
            )
        )
    return tuple(sorted(rows, key=lambda row: row.identity()))


def resolve_pit_authority(
    rows: Iterable[PITAuthorityRow], as_of: date
) -> tuple[PITAuthorityRow, ...]:
    """Resolve one non-superseded formal row per identity as of a date."""

    candidates: dict[tuple[str, str, str], list[PITAuthorityRow]] = defaultdict(list)
    materialized = tuple(rows)
    by_id = {row.authority_id: row for row in materialized}
    if len(by_id) != len(materialized):
        raise CalibrationFoundationError("PIT_AUTHORITY_DUPLICATE_ID")
    for row in materialized:
        if row.superseded_by_authority_id is not None:
            successor = by_id.get(row.superseded_by_authority_id)
            if successor is None or successor.identity() != row.identity():
                raise CalibrationFoundationError("PIT_AUTHORITY_INVALID_SUPERSESSION")
        if row.supersedes_authority_id is not None:
            predecessor = by_id.get(row.supersedes_authority_id)
            if predecessor is None or predecessor.identity() != row.identity():
                raise CalibrationFoundationError("PIT_AUTHORITY_INVALID_SUPERSESSION")
        if row.effective(as_of) and row.superseded_by_authority_id is None:
            candidates[row.identity()].append(row)

    resolved: list[PITAuthorityRow] = []
    for identity, matches in candidates.items():
        if len(matches) != 1:
            raise CalibrationFoundationError(
                f"PIT_AUTHORITY_CONFLICT:{identity[0]}:{identity[1]}:{identity[2]}"
            )
        resolved.append(matches[0])
    return tuple(sorted(resolved, key=lambda row: row.identity()))


@dataclass(frozen=True)
class _IndexBar:
    trading_date: date
    close: Decimal
    change: Decimal | None
    open: Decimal | None
    high: Decimal | None
    low: Decimal | None
    source_content_hash: str
    source_endpoint: str
    retrieved_at: datetime


@dataclass(frozen=True)
class BenchmarkFact:
    """One same-session official benchmark fact used by relative returns."""

    trading_date: date
    market: str
    benchmark_identity: str
    close: Decimal | None
    previous_close: Decimal | None
    return_pct: Decimal | None
    source_provider: str
    source_dataset: str
    source_endpoint: str
    source_content_hash: str
    retrieved_at: datetime
    data_status: str
    previous_close_basis: str
    adapter_version: str
    lineage: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "trading_date": self.trading_date.isoformat(),
            "market": self.market,
            "benchmark_identity": self.benchmark_identity,
            "close": str(self.close) if self.close is not None else None,
            "previous_close": (
                str(self.previous_close) if self.previous_close is not None else None
            ),
            "return_pct": str(self.return_pct) if self.return_pct is not None else None,
            "source_provider": self.source_provider,
            "source_dataset": self.source_dataset,
            "source_endpoint": self.source_endpoint,
            "source_content_hash": self.source_content_hash,
            "retrieved_at": self.retrieved_at.isoformat(),
            "data_status": self.data_status,
            "previous_close_basis": self.previous_close_basis,
            "adapter_version": self.adapter_version,
            "lineage": self.lineage,
        }


def parse_twse_month_payload(
    payload: object,
    *,
    source_endpoint: str,
    retrieved_at: datetime,
) -> tuple[_IndexBar, ...]:
    """Parse official TWSE MI_5MINS_HIST monthly OHLC rows."""

    if not isinstance(payload, Mapping) or str(payload.get("stat", "")).upper() != "OK":
        raise CalibrationFoundationError("TWSE_OFFICIAL_PAYLOAD_UNAVAILABLE")
    data = payload.get("data")
    if not isinstance(data, list):
        raise CalibrationFoundationError("TWSE_OFFICIAL_PAYLOAD_INVALID_DATA")
    content_hash = canonical_hash(payload)
    rows: list[_IndexBar] = []
    seen: set[date] = set()
    for raw in data:
        if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)) or len(raw) < 5:
            raise CalibrationFoundationError("TWSE_OFFICIAL_ROW_INVALID")
        trading_date = _exchange_date(raw[0])
        if trading_date in seen:
            raise CalibrationFoundationError("TWSE_OFFICIAL_DUPLICATE_DATE")
        seen.add(trading_date)
        values = tuple(_decimal(value, field) for value, field in zip(
            raw[1:5], ("open", "high", "low", "close"), strict=True
        ))
        open_, high, low, close = values
        if low > min(open_, high, close) or high < max(open_, low, close):
            raise CalibrationFoundationError("TWSE_OFFICIAL_INVALID_OHLC")
        rows.append(
            _IndexBar(
                trading_date=trading_date,
                close=close,
                change=None,
                open=open_,
                high=high,
                low=low,
                source_content_hash=content_hash,
                source_endpoint=source_endpoint,
                retrieved_at=retrieved_at,
            )
        )
    return tuple(sorted(rows, key=lambda row: row.trading_date))


def parse_tpex_month_payload(
    payload: object,
    *,
    source_endpoint: str,
    retrieved_at: datetime,
) -> tuple[_IndexBar, ...]:
    """Parse the official TPEx ``indexInfo/inx`` monthly report."""

    if not isinstance(payload, Mapping) or not isinstance(payload.get("tables"), list):
        raise CalibrationFoundationError("TPEX_OFFICIAL_PAYLOAD_INVALID")
    tables = payload["tables"]
    table = next((item for item in tables if isinstance(item, Mapping)), None)
    if table is None or not isinstance(table.get("data"), list):
        raise CalibrationFoundationError("TPEX_OFFICIAL_PAYLOAD_INVALID_DATA")
    content_hash = canonical_hash(payload)
    rows: list[_IndexBar] = []
    seen: set[date] = set()
    for raw in table["data"]:
        if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)) or len(raw) < 6:
            raise CalibrationFoundationError("TPEX_OFFICIAL_ROW_INVALID")
        trading_date = _exchange_date(raw[0])
        if trading_date in seen:
            raise CalibrationFoundationError("TPEX_OFFICIAL_DUPLICATE_DATE")
        seen.add(trading_date)
        open_, high, low, close = tuple(_decimal(value, field) for value, field in zip(
            raw[1:5], ("open", "high", "low", "close"), strict=True
        ))
        change = _decimal(raw[5], "change")
        if low > min(open_, high, close) or high < max(open_, low, close):
            raise CalibrationFoundationError("TPEX_OFFICIAL_INVALID_OHLC")
        rows.append(
            _IndexBar(
                trading_date=trading_date,
                close=close,
                change=change,
                open=open_,
                high=high,
                low=low,
                source_content_hash=content_hash,
                source_endpoint=source_endpoint,
                retrieved_at=retrieved_at,
            )
        )
    return tuple(sorted(rows, key=lambda row: row.trading_date))


def build_benchmark_facts(
    bars: Iterable[_IndexBar],
    *,
    market: str,
    from_date: date,
    to_date: date,
) -> tuple[BenchmarkFact, ...]:
    """Build validated same-session facts after cross-month previous-close joins."""

    ordered = sorted(tuple(bars), key=lambda row: row.trading_date)
    if len({row.trading_date for row in ordered}) != len(ordered):
        raise CalibrationFoundationError("BENCHMARK_DUPLICATE_DATE")
    if market == "TPE":
        identity = "TAIEX"
        provider = "TWSE"
        dataset = "indicesReport.MI_5MINS_HIST"
        adapter = "twse-official-taiex-history.v1"
        lineage = "TWSE official MI_5MINS_HIST -> TAIEX OHLC -> previous official session close"
    elif market == "TWO":
        identity = "TPEX_INDEX"
        provider = "TPEx"
        dataset = "indexInfo/inx"
        adapter = "tpex-official-index-history.v1"
        lineage = "TPEx official indexInfo/inx -> TPEx Index OHLC/change"
    else:
        raise CalibrationFoundationError(f"UNSUPPORTED_MARKET:{market}")

    facts: list[BenchmarkFact] = []
    for index, bar in enumerate(ordered):
        previous_close: Decimal | None
        basis: str
        if market == "TPE":
            previous_close = ordered[index - 1].close if index else None
            basis = "DERIVED_FROM_PREVIOUS_OFFICIAL_TAIEX_SESSION_CLOSE"
        else:
            previous_close = bar.close - bar.change if bar.change is not None else None
            basis = "DERIVED_FROM_OFFICIAL_CLOSE_AND_CHANGE"
        return_pct = None
        status = "AVAILABLE"
        if previous_close is None or previous_close <= 0:
            status = "MISSING_PREVIOUS_CLOSE"
        else:
            return_pct = (bar.close / previous_close - Decimal("1")) * Decimal("100")
        if from_date <= bar.trading_date <= to_date:
            facts.append(
                BenchmarkFact(
                    trading_date=bar.trading_date,
                    market=market,
                    benchmark_identity=identity,
                    close=bar.close,
                    previous_close=previous_close,
                    return_pct=return_pct,
                    source_provider=provider,
                    source_dataset=dataset,
                    source_endpoint=bar.source_endpoint,
                    source_content_hash=bar.source_content_hash,
                    retrieved_at=bar.retrieved_at,
                    data_status=status,
                    previous_close_basis=basis,
                    adapter_version=adapter,
                    lineage=lineage,
                )
            )
    return tuple(facts)


def authority_window(rows: Iterable[PITAuthorityRow]) -> tuple[date | None, date | None]:
    """Return the observed effective authority bounds."""

    materialized = tuple(rows)
    if not materialized:
        return None, None
    starts = [row.effective_from for row in materialized]
    ends = [row.effective_to for row in materialized if row.effective_to is not None]
    return min(starts), max(ends) if ends else None


def benchmark_window(facts: Iterable[BenchmarkFact]) -> tuple[date | None, date | None]:
    """Return the observed benchmark bounds for available facts."""

    available = [row.trading_date for row in facts if row.data_status == "AVAILABLE"]
    return (min(available), max(available)) if available else (None, None)


def benchmark_rows_by_date(
    facts: Iterable[BenchmarkFact],
) -> dict[date, dict[str, BenchmarkFact]]:
    """Group benchmark facts by date and fail closed on duplicate identities."""

    grouped: dict[date, dict[str, BenchmarkFact]] = defaultdict(dict)
    for fact in facts:
        if fact.benchmark_identity in grouped[fact.trading_date]:
            raise CalibrationFoundationError("BENCHMARK_DUPLICATE_IDENTITY_DATE")
        grouped[fact.trading_date][fact.benchmark_identity] = fact
    return dict(grouped)


def strict_join_member_day(
    *,
    trading_date: date,
    topic_id: str,
    market: str,
    instrument_code: str,
    close: Decimal | None,
    previous_close: Decimal | None,
    authority_rows: Iterable[PITAuthorityRow],
    benchmark_facts: Iterable[BenchmarkFact],
) -> dict[str, Any]:
    """Evaluate one member-day without relaxing any strict input requirement."""

    blockers: list[str] = []
    authority: PITAuthorityRow | None = None
    try:
        resolved = resolve_pit_authority(authority_rows, trading_date)
        authority = next(
            (
                row
                for row in resolved
                if row.identity() == (topic_id, market, instrument_code)
            ),
            None,
        )
    except CalibrationFoundationError:
        blockers.append("AUTHORITY_AMBIGUOUS")
    if authority is None and "AUTHORITY_AMBIGUOUS" not in blockers:
        blockers.append("ROLE_OR_MEMBERSHIP_MISSING")
    if close is None:
        blockers.append("MISSING_PRICE")
    if previous_close is None or previous_close <= 0:
        blockers.append("MISSING_PREVIOUS_CLOSE")

    expected_benchmark = "TAIEX" if market == "TPE" else "TPEX_INDEX"
    benchmark = next(
        (
            fact
            for fact in benchmark_facts
            if fact.trading_date == trading_date
            and fact.benchmark_identity == expected_benchmark
        ),
        None,
    )
    if benchmark is None or benchmark.data_status != "AVAILABLE":
        blockers.append("MISSING_BENCHMARK")
    elif benchmark.market != market:
        blockers.append("WRONG_MARKET_BENCHMARK")

    status = "STRICT_READY" if not blockers else blockers[0]
    return {
        "status": status,
        "blockers": tuple(blockers),
        "trading_date": trading_date.isoformat(),
        "topic_id": topic_id,
        "market": market,
        "instrument_code": instrument_code,
        "structural_role": authority.structural_role if authority else None,
        "benchmark_identity": benchmark.benchmark_identity if benchmark else None,
        "relative_return_pct": (
            str(
                (close / previous_close - Decimal("1")) * Decimal("100")
                - benchmark.return_pct
            )
            if (
                not blockers
                and close is not None
                and previous_close is not None
                and benchmark is not None
                and benchmark.return_pct is not None
            )
            else None
        ),
    }


__all__ = [
    "APPROVED",
    "CALIBRATION_FOUNDATION_VERSION",
    "PIT_AUTHORITY_SCHEMA_VERSION",
    "BenchmarkFact",
    "CalibrationFoundationError",
    "PITAuthorityRow",
    "authority_window",
    "benchmark_rows_by_date",
    "benchmark_window",
    "build_benchmark_facts",
    "canonical_hash",
    "load_pit_authority",
    "parse_tpex_month_payload",
    "parse_twse_month_payload",
    "resolve_pit_authority",
    "strict_join_member_day",
]
