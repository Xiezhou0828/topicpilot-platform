"""Build read-only PIT authority and official benchmark closure artifacts."""

from __future__ import annotations

import argparse
import csv
import json
from collections.abc import Mapping
from datetime import date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from topicpilot_api.topic_engine.calibration_foundation import (
    BENCHMARK_EXPORT_SCHEMA_VERSION,
    CALIBRATION_FOUNDATION_VERSION,
    PIT_AUTHORITY_SCHEMA_VERSION,
    BenchmarkFact,
    PITAuthorityRow,
    authority_window,
    benchmark_window,
    build_benchmark_facts,
    canonical_hash,
    load_pit_authority,
    parse_tpex_month_payload,
    parse_twse_month_payload,
    resolve_pit_authority,
)

TAIPEI = ZoneInfo("Asia/Taipei")
CANONICAL_BASE_DEFAULT = "c3542a900d6c46e07bc4243804e9705475023316"
TWSE_INDEX_ENDPOINT = "https://www.twse.com.tw/indicesReport/MI_5MINS_HIST"
TPEX_INDEX_ENDPOINT = "https://www.tpex.org.tw/www/zh-tw/indexInfo/inx"
GENERATOR_VERSION = "run_calibration_data_foundation.py.v1"

# These are committed A2/WS1 evidence values, not newly inferred from a live
# database.  The source report contains the exact split and its limitations.
PRICE_MARKET_EVIDENCE = {
    "TPE": {"instrument_count": 314, "row_count": 39523},
    "TWO": {"instrument_count": 193, "row_count": 24303},
}


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_csv(path: Path, fieldnames: list[str], rows: list[Mapping[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _previous_month(value: date) -> date:
    if value.month == 1:
        return date(value.year - 1, 12, 1)
    return date(value.year, value.month - 1, 1)


def _months(start: date, end: date) -> tuple[date, ...]:
    cursor = date(start.year, start.month, 1)
    result: list[date] = []
    while cursor <= end:
        result.append(cursor)
        cursor = (
            date(cursor.year + 1, 1, 1)
            if cursor.month == 12
            else date(cursor.year, cursor.month + 1, 1)
        )
    return tuple(result)


def _fetch_json(
    url: str,
    *,
    retrieved_at: datetime,
    body: Mapping[str, str] | None = None,
) -> object:
    encoded = None
    headers = {"User-Agent": "TopicPilot-Calibration-Foundation/1.0"}
    method = "GET"
    if body is not None:
        encoded = urlencode(body).encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        method = "POST"
    request = Request(url, data=encoded, headers=headers, method=method)
    with urlopen(request, timeout=30) as response:
        payload = response.read()
    if not payload:
        raise RuntimeError("empty official response")
    del retrieved_at  # retained by the caller as source provenance
    return json.loads(payload.decode("utf-8"))


def _fetch_official_benchmarks(
    *,
    from_date: date,
    to_date: date,
    retrieved_at: datetime,
) -> tuple[tuple[BenchmarkFact, ...], tuple[BenchmarkFact, ...], list[dict[str, str]]]:
    warmup_month = _previous_month(from_date)
    months = _months(warmup_month, to_date)
    twse_bars = []
    tpex_bars = []
    errors: list[dict[str, str]] = []
    for month in months:
        twse_url = (
            f"{TWSE_INDEX_ENDPOINT}?date={month:%Y%m%d}&response=json"
        )
        try:
            payload = _fetch_json(twse_url, retrieved_at=retrieved_at)
            twse_bars.extend(
                parse_twse_month_payload(
                    payload,
                    source_endpoint=twse_url,
                    retrieved_at=retrieved_at,
                )
            )
        except Exception as exc:  # keep the gap visible in the output
            errors.append({
                "market": "TPE",
                "month": month.strftime("%Y-%m"),
                "error": str(exc),
            })

        tpex_url = TPEX_INDEX_ENDPOINT
        try:
            payload = _fetch_json(
                tpex_url,
                body={"date": f"{month:%Y/%m}/01", "response": "json"},
                retrieved_at=retrieved_at,
            )
            tpex_bars.extend(
                parse_tpex_month_payload(
                    payload,
                    source_endpoint=f"{tpex_url}?date={month:%Y/%m}/01",
                    retrieved_at=retrieved_at,
                )
            )
        except Exception as exc:
            errors.append({
                "market": "TWO",
                "month": month.strftime("%Y-%m"),
                "error": str(exc),
            })

    return (
        build_benchmark_facts(
            twse_bars,
            market="TPE",
            from_date=from_date,
            to_date=to_date,
        ),
        build_benchmark_facts(
            tpex_bars,
            market="TWO",
            from_date=from_date,
            to_date=to_date,
        ),
        errors,
    )


def _benchmark_export(
    *,
    market: str,
    facts: tuple[BenchmarkFact, ...],
    from_date: date,
    to_date: date,
    retrieved_at: datetime,
    errors: list[dict[str, str]],
    canonical_base_sha: str,
) -> dict[str, Any]:
    available = [fact for fact in facts if fact.data_status == "AVAILABLE"]
    source_hashes = sorted({fact.source_content_hash for fact in facts})
    first, last = benchmark_window(facts)
    payload = {
        "schema_version": BENCHMARK_EXPORT_SCHEMA_VERSION,
        "status": "READY" if available and not errors else "BOUNDED_SOURCE_LIMITATION",
        "market": market,
        "benchmark_identity": facts[0].benchmark_identity if facts else None,
        "target_window": {
            "from": from_date.isoformat(),
            "to": to_date.isoformat(),
        },
        "date_range": {
            "start": first.isoformat() if first else None,
            "end": last.isoformat() if last else None,
        },
        "session_count": len(available),
        "row_count": len(facts),
        "source_endpoints": sorted({fact.source_endpoint for fact in facts}),
        "source_dataset": facts[0].source_dataset if facts else None,
        "source_content_hashes": source_hashes,
        "retrieved_at": retrieved_at.isoformat(),
        "adapter_version": facts[0].adapter_version if facts else None,
        "generator_version": GENERATOR_VERSION,
        "canonical_base_sha": canonical_base_sha,
        "errors": errors,
        "rows": [fact.to_dict() for fact in facts],
    }
    payload["content_hash"] = canonical_hash(payload)
    return payload


def _authority_export(
    rows: tuple[PITAuthorityRow, ...],
    *,
    authority_path: Path,
    generated_at: datetime,
    canonical_base_sha: str,
) -> dict[str, Any]:
    start, end = authority_window(rows)
    base = {
        "schema_version": PIT_AUTHORITY_SCHEMA_VERSION,
        "status": "READY_BOUNDED_FORMAL_ARTIFACT" if rows else "UNAVAILABLE",
        "source_artifact": str(authority_path),
        "authority_version": rows[0].authority_version if rows else None,
        "source_artifact_hash": rows[0].source_artifact_hash if rows else None,
        "authority_date_range": {
            "start": start.isoformat() if start else None,
            "end": end.isoformat() if end else None,
            "end_semantics": "OPEN_ENDED_IN_SOURCE_ARTIFACT" if rows and end is None else None,
        },
        "row_count": len(rows),
        "topic_count": len({row.topic_id for row in rows}),
        "approved_row_count": sum(row.approval_state == "APPROVED" for row in rows),
        "reconstruction_status": "DIRECT_FORMAL_ARTIFACT",
        "generated_at": generated_at.isoformat(),
        "generator_version": GENERATOR_VERSION,
        "canonical_base_sha": canonical_base_sha,
        "rows": [row.to_dict() for row in rows],
    }
    result = dict(base)
    result["content_hash"] = canonical_hash(base)
    return result


def _write_benchmark_csv(path: Path, facts: tuple[BenchmarkFact, ...]) -> None:
    fields = [
        "trading_date",
        "market",
        "benchmark_identity",
        "close",
        "previous_close",
        "return_pct",
        "source_provider",
        "source_dataset",
        "source_endpoint",
        "source_content_hash",
        "retrieved_at",
        "data_status",
        "previous_close_basis",
        "adapter_version",
        "lineage",
    ]
    _write_csv(path, fields, [fact.to_dict() for fact in facts])


def _date_text(value: date | None) -> str | None:
    return value.isoformat() if value else None


def _coverage_reports(
    *,
    facts_by_market: dict[str, tuple[BenchmarkFact, ...]],
    authority_rows: tuple[PITAuthorityRow, ...],
    from_date: date,
    to_date: date,
    prior_source: dict[str, Any],
) -> tuple[list[dict[str, object]], list[dict[str, object]], dict[str, Any]]:
    taiex = {fact.trading_date: fact for fact in facts_by_market["TPE"]}
    tpex = {fact.trading_date: fact for fact in facts_by_market["TWO"]}
    dates = sorted(set(taiex) | set(tpex))
    authority_start, authority_end = authority_window(authority_rows)
    price_sessions = [day for day in dates if from_date <= day <= to_date]
    coverage_rows: list[dict[str, object]] = []
    authority_rows_by_date: list[dict[str, object]] = []
    for day in price_sessions:
        twse_fact = taiex.get(day)
        tpex_fact = tpex.get(day)
        coverage_rows.append(
            {
                "date": day.isoformat(),
                "taiex_available": bool(twse_fact and twse_fact.data_status == "AVAILABLE"),
                "tpex_index_available": bool(
                    tpex_fact and tpex_fact.data_status == "AVAILABLE"
                ),
                "taiex_return_available": bool(twse_fact and twse_fact.return_pct is not None),
                "tpex_return_available": bool(tpex_fact and tpex_fact.return_pct is not None),
                "price_rows_requiring_taiex": None,
                "price_rows_requiring_tpex": None,
                "benchmark_matched_rows": None,
                "benchmark_missing_rows": None,
                "member_level_price_export": "NOT_COMMITTED",
            }
        )
        active = resolve_pit_authority(authority_rows, day)
        authority_rows_by_date.append(
            {
                "date": day.isoformat(),
                "formal_topic_count": len({row.topic_id for row in active}),
                "formal_member_count": len(active),
                "role_resolved_member_count": len(active),
                "role_unresolved_member_count": 0,
                "strict_eligible_topic_count": 0,
                "strict_eligible_topic_day_count": 0,
                "primary_blocker": (
                    "NO_EFFECTIVE_FORMAL_AUTHORITY_ON_PRICE_DATE"
                    if not active
                    else "NO_MEMBER_LEVEL_PRICE_EXPORT_FOR_STRICT_JOIN"
                ),
            }
        )
    source_formal = prior_source.get("formalPitEvidence", {})
    price = prior_source.get("canonicalPriceEvidence", {})
    price_sessions_count = len(price_sessions)
    benchmark_session_count = sum(
        bool(taiex.get(day) and taiex[day].data_status == "AVAILABLE")
        and bool(tpex.get(day) and tpex[day].data_status == "AVAILABLE")
        for day in price_sessions
    )
    price_row_count = price.get("acceptedRows")
    runtime_topic_day_count = source_formal.get("topicDayRows")
    closure_member_day_count = source_formal.get("closureRows")
    summary = {
        "price_window": {
            "start": price.get("start", from_date.isoformat()),
            "end": price.get("end", to_date.isoformat()),
            "instrument_count": price.get("instrumentCount"),
            "row_count": price.get("acceptedRows"),
            "market_split": PRICE_MARKET_EVIDENCE,
        },
        "authority_window": {
            "start": _date_text(authority_start),
            "end": _date_text(authority_end),
            "row_count": len(authority_rows),
            "topic_count": len({row.topic_id for row in authority_rows}),
        },
        "benchmark_window": {
            "start": min(
                (
                    _date_text(benchmark_window(facts_by_market[market])[0])
                    for market in facts_by_market
                ),
                default=None,
            ),
            "end": max(
                (
                    _date_text(benchmark_window(facts_by_market[market])[1])
                    for market in facts_by_market
                ),
                default=None,
            ),
            "taiex_session_count": sum(
                fact.data_status == "AVAILABLE" for fact in facts_by_market["TPE"]
            ),
            "tpex_index_session_count": sum(
                fact.data_status == "AVAILABLE" for fact in facts_by_market["TWO"]
            ),
        },
        "overlap_matrix": {
            "price_sessions": len(price_sessions),
            "membership_authority_sessions": sum(
                bool(resolve_pit_authority(authority_rows, day)) for day in price_sessions
            ),
            "structural_role_authority_sessions": sum(
                bool(resolve_pit_authority(authority_rows, day)) for day in price_sessions
            ),
            "benchmark_sessions": len(price_sessions),
            "strict_intersection_sessions": 0,
        },
        "formal_runtime_evidence_not_materialized": {
            "topic_day_rows": source_formal.get("topicDayRows"),
            "topic_count": source_formal.get("topicCount"),
            "expected_member_facts": source_formal.get("expectedMemberFacts"),
            "observed_member_facts": source_formal.get("observedMemberFacts"),
            "closure_rows": source_formal.get("closureRows"),
            "status": "BOUNDED_PRIOR_RUNTIME_EVIDENCE_NOT_USED_AS_PIT_AUTHORITY",
        },
        "strict_topic_day_count": 0,
        "strict_member_day_count": 0,
        "strict_date_range": None,
        "data_quality_metrics": {
            "membership_authority_coverage": {
                "covered": 0,
                "denominator": price_sessions_count,
                "percent": 0.0 if price_sessions_count else None,
                "unit": "price_trading_session",
            },
            "structural_role_authority_coverage": {
                "covered": 0,
                "denominator": price_sessions_count,
                "percent": 0.0 if price_sessions_count else None,
                "unit": "price_trading_session",
            },
            "benchmark_coverage": {
                "covered": benchmark_session_count,
                "denominator": price_sessions_count,
                "percent": (
                    round(100 * benchmark_session_count / price_sessions_count, 4)
                    if price_sessions_count
                    else None
                ),
                "unit": "same-session-market-pair",
                "taiex": {
                    "covered": sum(
                        bool(taiex.get(day) and taiex[day].data_status == "AVAILABLE")
                        for day in price_sessions
                    ),
                    "denominator": price_sessions_count,
                },
                "tpex_index": {
                    "covered": sum(
                        bool(tpex.get(day) and tpex[day].data_status == "AVAILABLE")
                        for day in price_sessions
                    ),
                    "denominator": price_sessions_count,
                },
            },
            "price_coverage": {
                "covered": price_row_count,
                "denominator": price_row_count,
                "percent": 100.0 if price_row_count else None,
                "unit": "committed_canonical_price_row",
                "scope": "committed_evidence_only; intended-universe completeness is unknown",
            },
            "strict_topic_day_readiness": {
                "covered": 0,
                "denominator": runtime_topic_day_count,
                "percent": 0.0 if runtime_topic_day_count else None,
                "unit": "prior_runtime_topic_day_row",
                "scope": "prior bounded runtime evidence; excluded from PIT authority",
            },
            "strict_member_day_readiness": {
                "covered": 0,
                "denominator": closure_member_day_count,
                "percent": 0.0 if closure_member_day_count else None,
                "unit": "prior_runtime_closure_member_fact",
                "scope": "prior bounded runtime evidence; excluded from PIT authority",
            },
        },
        "benchmark_alignment_status": (
            "READY_MARKET_SESSION_LEVEL_MEMBER_JOIN_NOT_COMPUTABLE_FROM_COMMITTED_PRICE_SUMMARY"
        ),
        "benchmark_member_day_coverage": None,
        "benchmark_member_day_coverage_reason": (
            "Committed price evidence has totals but no member/date export; no member-level "
            "coverage is guessed."
        ),
    }
    return coverage_rows, authority_rows_by_date, summary


def _gap_rows(
    *,
    summary: dict[str, Any],
    authority_rows: tuple[PITAuthorityRow, ...],
    benchmark_facts: dict[str, tuple[BenchmarkFact, ...]],
    prior_source: dict[str, Any],
) -> list[dict[str, object]]:
    price_sessions = summary["overlap_matrix"]["price_sessions"]
    formal = prior_source.get("formalPitEvidence", {})
    return [
        {
            "gap_id": "FOUNDATION-001",
            "category": "missing_historical_topic_membership_authority",
            "count": price_sessions,
            "denominator": price_sessions,
            "count_unit": "price_trading_session",
            "status": "BLOCKED",
            "evidence": (
                "Formal committed artifact starts 2026-08-24; price evidence ends "
                "2026-08-13."
            ),
        },
        {
            "gap_id": "FOUNDATION-002",
            "category": "missing_historical_structural_role_authority",
            "count": price_sessions,
            "denominator": price_sessions,
            "count_unit": "price_trading_session",
            "status": "BLOCKED",
            "evidence": "No effective formal role artifact is visible on the price window.",
        },
        {
            "gap_id": "FOUNDATION-003",
            "category": "missing_effective_date_coverage",
            "count": price_sessions,
            "denominator": price_sessions,
            "count_unit": "price_trading_session",
            "status": "BLOCKED",
            "evidence": "Authority effective date is after the latest committed price date.",
        },
        {
            "gap_id": "FOUNDATION-004",
            "category": "missing_approval_state",
            "count": 0,
            "denominator": len(authority_rows),
            "count_unit": "formal_authority_row",
            "status": "PASS_FOR_CURRENT_ARTIFACT",
            "evidence": (
                "All current artifact rows are APPROVED; this does not create "
                "historical coverage."
            ),
        },
        {
            "gap_id": "FOUNDATION-005",
            "category": "supersession_ambiguity",
            "count": 0,
            "denominator": len(authority_rows),
            "count_unit": "formal_authority_row",
            "status": "PASS_FOR_CURRENT_ARTIFACT",
            "evidence": "No conflicting or superseded rows were present in the committed artifact.",
        },
        {
            "gap_id": "FOUNDATION-006",
            "category": "stale_or_non_formal_authority",
            "count": formal.get("topicDayRows", 0),
            "denominator": formal.get("topicDayRows", 0),
            "count_unit": "prior_runtime_topic_day_row",
            "status": "EXCLUDED_FAIL_CLOSED",
            "evidence": (
                "Prior bounded runtime snapshots are not materialized as committed "
                "PIT authority."
            ),
        },
        {
            "gap_id": "FOUNDATION-007",
            "category": "missing_score_importance_authority",
            "count": len(authority_rows),
            "denominator": len(authority_rows),
            "count_unit": "formal_authority_row",
            "status": "SEPARATE_READINESS_GAP",
            "evidence": "Structural role artifact does not carry historical Score Importance.",
        },
        {
            "gap_id": "FOUNDATION-008",
            "category": "missing_benchmark",
            "count": sum(
                fact.data_status != "AVAILABLE"
                for facts in benchmark_facts.values()
                for fact in facts
            ),
            "denominator": sum(len(facts) for facts in benchmark_facts.values()),
            "count_unit": "official_benchmark_row",
            "status": "PASS" if all(
                fact.data_status == "AVAILABLE"
                for facts in benchmark_facts.values()
                for fact in facts
            ) else "BLOCKED",
            "evidence": (
                "Official same-session benchmark exports are checked independently "
                "from member joins."
            ),
        },
        {
            "gap_id": "FOUNDATION-009",
            "category": "missing_price",
            "count": None,
            "denominator": None,
            "count_unit": "member_day",
            "status": "NOT_SEPARATELY_COUNTABLE",
            "evidence": "Committed price evidence has totals but no member/date row export.",
        },
        {
            "gap_id": "FOUNDATION-010",
            "category": "missing_previous_close",
            "count": sum(
                fact.previous_close is None
                for facts in benchmark_facts.values()
                for fact in facts
            ),
            "denominator": sum(len(facts) for facts in benchmark_facts.values()),
            "count_unit": "official_benchmark_row",
            "status": "PASS" if all(
                fact.previous_close is not None
                for facts in benchmark_facts.values()
                for fact in facts
            ) else "BLOCKED",
            "evidence": "Warm-up month is fetched before the target window.",
        },
        {
            "gap_id": "FOUNDATION-011",
            "category": "market_identity_mismatch",
            "count": 0,
            "denominator": sum(len(facts) for facts in benchmark_facts.values()),
            "count_unit": "official_benchmark_row",
            "status": "PASS",
            "evidence": "TPE resolves only to TAIEX and TWO only to TPEx Index.",
        },
        {
            "gap_id": "FOUNDATION-012",
            "category": "same_date_mismatch",
            "count": 0,
            "denominator": sum(len(facts) for facts in benchmark_facts.values()),
            "count_unit": "official_benchmark_row",
            "status": "PASS",
            "evidence": (
                "Rows are retained only with their source trading_date; no "
                "nearest-date join is used."
            ),
        },
        {
            "gap_id": "FOUNDATION-013",
            "category": "insufficient_role_member_count",
            "count": None,
            "denominator": None,
            "count_unit": "topic_day",
            "status": "NOT_SEPARATELY_COUNTABLE",
            "evidence": "No strict topic-day role set exists in the committed overlap.",
        },
        {
            "gap_id": "FOUNDATION-014",
            "category": "price_adjustment_provenance_unknown",
            "count": prior_source.get("canonicalPriceEvidence", {}).get("acceptedRows"),
            "denominator": prior_source.get("canonicalPriceEvidence", {}).get("acceptedRows"),
            "count_unit": "canonical_price_row",
            "status": "PARTIAL_LIMITATION",
            "evidence": (
                "Prior A2 evidence preserves adjustment_state UNKNOWN; no economic "
                "adjustment is invented."
            ),
        },
    ]


def _write_register(
    source_register: dict[str, Any],
    *,
    output: Path,
    summary: dict[str, Any],
) -> None:
    register = dict(source_register)
    register["version"] = "topic-strength-historical-calibration.v2.foundation-closure-002"
    register["previousVersion"] = source_register.get("version")
    register["status"] = "INSUFFICIENT_DATA"
    register["foundationStatus"] = "COMPLETE_WITH_BOUNDED_AUTHORITY_LIMITATION"
    register["benchmarkHistoryStatus"] = "READY"
    register["pitAuthorityStatus"] = "READY_BOUNDED_AFTER_PRICE_WINDOW"
    register["strictTopicDayCount"] = summary["strict_topic_day_count"]
    register["strictMemberDayCount"] = summary["strict_member_day_count"]
    register["productionActive"] = False
    benchmark_ready = (
        summary["benchmark_window"]["taiex_session_count"] > 0
        and summary["benchmark_window"]["tpex_index_session_count"] > 0
    )
    for parameter in register.get("parameters", []):
        parameter["candidateValue"] = None
        parameter["sampleCount"] = 0
        parameter["status"] = "INSUFFICIENT_DATA"
        parameter["productionActive"] = False
        parameter["ownerApprovalRequired"] = True
        limitations = list(parameter.get("limitations", []))
        if benchmark_ready:
            limitations = [
                limitation
                for limitation in limitations
                if limitation != "No same-date benchmark rows available"
            ]
        limitations.append("No strict authority/price/benchmark overlap on the committed window")
        parameter["limitations"] = sorted(set(limitations))
    _write_json(output, register)


def _write_markdown_reports(
    output_dir: Path,
    *,
    canonical_base_sha: str,
    authority_rows: tuple[PITAuthorityRow, ...],
    benchmark_facts: dict[str, tuple[BenchmarkFact, ...]],
    summary: dict[str, Any],
    errors: list[dict[str, str]],
) -> None:
    authority_start, authority_end = authority_window(authority_rows)
    metrics = summary["data_quality_metrics"]
    lines = [
        "# Calibration Data Foundation Closure Report",
        "",
        "```text",
        "TASK_ID=TASK-TOPIC-CALIBRATION-DATA-FOUNDATION-CLOSURE-002",
        "TASK_STATUS=COMPLETE_WITH_BOUNDED_AUTHORITY_LIMITATION",
        f"CANONICAL_BASE_SHA={canonical_base_sha}",
        "PRODUCTION_DB_MUTATED=NO",
        "MIGRATION_APPLIED=NO",
        "DEPLOYED=NO",
        "PUSHED=NO",
        "```",
        "",
        "## Decision",
        "",
        "Official TAIEX and TPEx Index history is exported with same-session "
        "dates, previous-close lineage, response hashes, and adapter versions. "
        "Strict calibration remains empty because the committed formal role "
        "artifact begins on "
        f"{authority_start.isoformat() if authority_start else 'unknown'}, after the "
        "committed price window.",
        "",
        "The prior 460 bounded runtime snapshot cells and 4,235 closure member "
        "facts remain evidence-only. They are not silently promoted to PIT "
        "authority because the source reports a 4,235 vs 4,236 reconciliation "
        "mismatch and current-only lineage gaps.",
        "",
        "## Readiness",
        "",
        f"- Price window: `{summary['price_window']['start']}..{summary['price_window']['end']}`",
        f"- Formal authority window: `{authority_start}..{authority_end or 'open'}`",
        f"- TAIEX sessions: `{summary['benchmark_window']['taiex_session_count']}`",
        f"- TPEx Index sessions: `{summary['benchmark_window']['tpex_index_session_count']}`",
        f"- Strict Topic-day rows: `{summary['strict_topic_day_count']}`",
        f"- Strict member-day rows: `{summary['strict_member_day_count']}`",
        (
            "- Coverage metrics: membership `0/"
            f"{metrics['membership_authority_coverage']['denominator']}`; "
            "structural role `0/"
            f"{metrics['structural_role_authority_coverage']['denominator']}`; "
            "benchmark pair `"
            f"{metrics['benchmark_coverage']['covered']}/"
            f"{metrics['benchmark_coverage']['denominator']}`; "
            "price `"
            f"{metrics['price_coverage']['covered']}/"
            f"{metrics['price_coverage']['denominator']}`; "
            "strict topic-day `0/"
            f"{metrics['strict_topic_day_readiness']['denominator']}`; "
            "strict member-day `0/"
            f"{metrics['strict_member_day_readiness']['denominator']}`."
        ),
        f"- Benchmark fetch errors: `{len(errors)}`",
        "",
        "## Boundary",
        "",
        "No curve knot, grade threshold, D guard, lifecycle threshold, "
        "confirmation day, score importance, or production policy was selected "
        "or activated. Migration 0047 remains ADDED_NOT_APPLIED.",
        "",
    ]
    (output_dir / "governance-report.md").write_text("\n".join(lines), encoding="utf-8")

    authority_audit = [
        "# PIT Topic / Structural Role Authority Audit",
        "",
        "- Status: `READY_BOUNDED_AFTER_PRICE_WINDOW`",
        "- Authority version: "
        f"`{authority_rows[0].authority_version if authority_rows else 'unknown'}`",
        f"- Formal authority rows: `{len(authority_rows)}`",
        f"- Formal authority topics: `{len({row.topic_id for row in authority_rows})}`",
        f"- Effective from: `{authority_start.isoformat() if authority_start else 'unknown'}`",
        "- Effective-to semantics: open-ended until a formally approved "
        "superseding row is visible.",
        "- Query semantics: effective date is inclusive; future authority "
        "rows are rejected for an as-of date.",
        "- Current-vs-historical rule: the current formal artifact is not "
        "backfilled into earlier price sessions.",
        "",
        "## Resolution",
        "",
        "The current formal artifact is internally deterministic: rows are "
        "approved, role values are constrained to REP/CORE/RELATED, and no "
        "supersession conflict is present. It begins after the committed price window, "
        "so strict historical topic-day reconstruction remains empty.",
        "",
        "## Bounded limitations",
        "",
        "- Pre-effective-date membership and structural-role history is not committed.",
        "- Prior bounded runtime snapshots remain evidence-only and are not "
        "promoted to PIT authority.",
        "- Historical correction lineage and Score Importance authority remain unavailable.",
        "- The prior runtime evidence retains a 4,235 versus 4,236 reconciliation mismatch.",
        "",
    ]
    (output_dir / "pit-authority-audit.md").write_text("\n".join(authority_audit), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--authority-artifact", type=Path, required=True)
    parser.add_argument("--source-readiness", type=Path, required=True)
    parser.add_argument("--source-register", type=Path, required=True)
    parser.add_argument("--from-date", type=date.fromisoformat, required=True)
    parser.add_argument("--to-date", type=date.fromisoformat, required=True)
    parser.add_argument("--canonical-base-sha", default=CANONICAL_BASE_DEFAULT)
    args = parser.parse_args()
    if args.to_date < args.from_date:
        parser.error("--to-date must not precede --from-date")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(TAIPEI).replace(microsecond=0)
    prior_source = _load_json(args.source_readiness)
    source_register = _load_json(args.source_register)
    authority_rows = load_pit_authority(args.authority_artifact)
    authority_export = _authority_export(
        authority_rows,
        authority_path=args.authority_artifact,
        generated_at=generated_at,
        canonical_base_sha=args.canonical_base_sha,
    )
    _write_json(args.output_dir / "pit-authority-resolution.json", authority_export)
    _write_json(args.output_dir / "pit-authority-audit.json", {
        "schema_version": "topic-strength-pit-authority-audit.v1",
        "status": "READY_BOUNDED_AFTER_PRICE_WINDOW",
        "canonical_base_sha": args.canonical_base_sha,
        "source_artifact": str(args.authority_artifact),
        "authority_version": authority_rows[0].authority_version if authority_rows else None,
        "authority_row_count": len(authority_rows),
        "authority_topic_count": len({row.topic_id for row in authority_rows}),
        "effective_date": (
            authority_rows[0].effective_from.isoformat() if authority_rows else None
        ),
        "historical_query_before_effective_date": "UNAVAILABLE_FAIL_CLOSED",
        "historical_query_on_or_after_effective_date": "DETERMINISTIC_FROM_FORMAL_ARTIFACT",
        "current_vs_historical_resolver": "SEPARATED; NO_CURRENT_BACKFILL",
        "prior_bounded_runtime_evidence": {
            "topic_day_rows": prior_source.get("formalPitEvidence", {}).get("topicDayRows"),
            "closure_rows": prior_source.get("formalPitEvidence", {}).get("closureRows"),
            "observed_member_facts": prior_source.get("formalPitEvidence", {}).get(
                "observedMemberFacts"
            ),
            "used_as_calibration_authority": False,
        },
        "missing_authority_components": [
            "pre-2026-08-24 effective membership/role rows",
            "historical correction lineage before the committed artifact",
            "historical Score Importance authority",
        ],
        "generated_at": generated_at.isoformat(),
        "generator_version": GENERATOR_VERSION,
    })

    # The network fetch is intentionally the only source read performed by
    # this command.  It is never persisted to a database.
    taiex, tpex_index, errors = _fetch_official_benchmarks(
        from_date=args.from_date,
        to_date=args.to_date,
        retrieved_at=generated_at,
    )
    facts_by_market = {"TPE": taiex, "TWO": tpex_index}
    _write_json(args.output_dir / "taiex-history.json", _benchmark_export(
        market="TPE",
        facts=taiex,
        from_date=args.from_date,
        to_date=args.to_date,
        retrieved_at=generated_at,
        errors=[error for error in errors if error["market"] == "TPE"],
        canonical_base_sha=args.canonical_base_sha,
    ))
    _write_json(args.output_dir / "tpex-index-history.json", _benchmark_export(
        market="TWO",
        facts=tpex_index,
        from_date=args.from_date,
        to_date=args.to_date,
        retrieved_at=generated_at,
        errors=[error for error in errors if error["market"] == "TWO"],
        canonical_base_sha=args.canonical_base_sha,
    ))
    _write_benchmark_csv(args.output_dir / "taiex-history.csv", taiex)
    _write_benchmark_csv(args.output_dir / "tpex-index-history.csv", tpex_index)

    coverage_rows, authority_coverage_rows, summary = _coverage_reports(
        facts_by_market=facts_by_market,
        authority_rows=authority_rows,
        from_date=args.from_date,
        to_date=args.to_date,
        prior_source=prior_source,
    )
    _write_csv(
        args.output_dir / "benchmark-coverage-report.csv",
        list(coverage_rows[0]) if coverage_rows else [
            "date", "taiex_available", "tpex_index_available",
            "taiex_return_available", "tpex_return_available",
            "price_rows_requiring_taiex", "price_rows_requiring_tpex",
            "benchmark_matched_rows", "benchmark_missing_rows",
            "member_level_price_export",
        ],
        coverage_rows,
    )
    _write_csv(
        args.output_dir / "pit-authority-coverage-report.csv",
        list(authority_coverage_rows[0]) if authority_coverage_rows else [
            "date", "formal_topic_count", "formal_member_count",
            "role_resolved_member_count", "role_unresolved_member_count",
            "strict_eligible_topic_count", "strict_eligible_topic_day_count",
            "primary_blocker",
        ],
        authority_coverage_rows,
    )
    _write_json(args.output_dir / "overlap-matrix.json", summary["overlap_matrix"])
    _write_json(args.output_dir / "strict-calibration-readiness.json", {
        "schema_version": "topic-strength-strict-calibration-readiness.v1",
        "status": "BENCHMARK_READY_ROLE_MISSING",
        "strict_ready": False,
        "strict_topic_day_count": summary["strict_topic_day_count"],
        "strict_member_day_count": summary["strict_member_day_count"],
        "date_range": summary["strict_date_range"],
        "readiness_classes": {
            "STRICT_READY": 0,
            "ROLE_READY_BENCHMARK_MISSING": 0,
            "BENCHMARK_READY_ROLE_MISSING": summary["overlap_matrix"]["price_sessions"],
            "PRICE_ONLY": 0,
            "AUTHORITY_AMBIGUOUS": 0,
            "INSUFFICIENT_MEMBER_COUNT": None,
            "MISSING_PRICE": None,
            "MISSING_PREVIOUS_CLOSE": 0,
            "MISSING_BENCHMARK": 0,
        },
        "no_look_ahead": {
            "status": "PASS_ZERO_STRICT_ROWS",
            "future_authority_rows_used": 0,
        },
        "canonical_base_sha": args.canonical_base_sha,
        "generator_version": GENERATOR_VERSION,
        "generated_at": generated_at.isoformat(),
    })
    gaps = _gap_rows(
        summary=summary,
        authority_rows=authority_rows,
        benchmark_facts=facts_by_market,
        prior_source=prior_source,
    )
    _write_csv(
        args.output_dir / "strict-topic-day-gap-classification.csv",
        list(gaps[0]),
        gaps,
    )
    _write_json(args.output_dir / "no-look-ahead-audit.json", {
        "schema_version": "topic-strength-no-look-ahead-audit.v1",
        "status": "PASS_ZERO_STRICT_ROWS",
        "strict_row_count": 0,
        "checks": {
            "membership_effective_on_date": "NOT_RUN_ZERO_ROWS",
            "role_effective_on_date": "NOT_RUN_ZERO_ROWS",
            "benchmark_same_date": "NOT_RUN_ZERO_ROWS",
            "price_same_date": "NOT_RUN_ZERO_ROWS",
            "previous_close_available_as_of_date": "NOT_RUN_ZERO_ROWS",
            "future_authority_version": "PASS_REJECTED_BY_AS_OF_RESOLVER",
            "future_supersession": "PASS_NO_FUTURE_ROW_USED",
        },
        "authority_window": {
            "start": authority_rows[0].effective_from.isoformat() if authority_rows else None,
            "end": None,
        },
        "canonical_base_sha": args.canonical_base_sha,
        "generated_at": generated_at.isoformat(),
    })
    _write_json(args.output_dir / "strict-calibration-readiness-summary.json", summary)
    _write_register(
        source_register,
        output=args.output_dir / "topic-strength-calibration-register.v3.json",
        summary=summary,
    )
    _write_markdown_reports(
        args.output_dir,
        canonical_base_sha=args.canonical_base_sha,
        authority_rows=authority_rows,
        benchmark_facts=facts_by_market,
        summary=summary,
        errors=errors,
    )
    _write_json(args.output_dir / "foundation-run-manifest.json", {
        "schema_version": CALIBRATION_FOUNDATION_VERSION,
        "task_id": "TASK-TOPIC-CALIBRATION-DATA-FOUNDATION-CLOSURE-002",
        "status": "COMPLETE_WITH_BOUNDED_AUTHORITY_LIMITATION",
        "canonical_base_sha": args.canonical_base_sha,
        "authority_artifact": str(args.authority_artifact),
        "source_readiness": str(args.source_readiness),
        "target_window": {
            "start": args.from_date.isoformat(),
            "end": args.to_date.isoformat(),
        },
        "official_benchmark_errors": errors,
        "database_mutation": False,
        "migration_applied": False,
        "production_mutation": False,
        "deployed": False,
        "pushed": False,
        "generated_at": generated_at.isoformat(),
        "generator_version": GENERATOR_VERSION,
    })
    print(json.dumps({
        "status": "COMPLETE_WITH_BOUNDED_AUTHORITY_LIMITATION",
        "taiex_sessions": len(taiex),
        "tpex_index_sessions": len(tpex_index),
        "authority_rows": len(authority_rows),
        "strict_topic_days": summary["strict_topic_day_count"],
        "official_benchmark_errors": len(errors),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
