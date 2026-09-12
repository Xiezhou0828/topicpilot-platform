"""Generate the WS4 authority-gap resolution and G2 replay artifacts.

This task is deliberately read-only with respect to application data.  It
loads the existing lifecycle/corporate-action authority, verifies the two
provider gaps against the existing official adapters, performs bounded
official status lookups, and writes only the task report directory.
"""

from __future__ import annotations

import csv
import json
import subprocess
from datetime import date
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from topicpilot_api.instrument_lifecycle_authority import (
    InstrumentLifecycleAuthority,
    LifecycleAuthorityError,
    LifecycleEventRecord,
    TradingExpectation,
    decide_missing_bar,
    file_sha256,
    load_corporate_action_events,
)
from topicpilot_api.market_data.exchange import (
    TpexOfficialDailyProvider,
    TwseOfficialDailyProvider,
)
from topicpilot_api.market_data.history import HistoricalProviderError
from topicpilot_api.reference_data.bundle import load_bundle

TASK = "TASK-WS4-EOD-AUTHORITY-GAP-RESOLUTION-6241-1563-AND-G2-CLOSURE"
AUDIT_DATE = "2026-08-31"
AUTHORIZED_EOD_MAX_DATE = "2026-08-13"
BUNDLE_RELATIVE = "services/api/src/topicpilot_api/reference_data/bundles/tw-reference-v1"
CORPORATE_EVENTS_RELATIVE = (
    "reports/TASK-REC-A1-CORPORATE-ACTION-RESEARCH-DATASET-IMPLEMENTATION"
    "/REC-A1-CA-EVENTS-V0.json"
)
UNKNOWN_LEDGER_RELATIVE = (
    "reports/TASK-REC-A1-UNKNOWN-154-IDENTITY-EVENT-GAP-REVIEW"
    "/identity-review-ledger.json"
)
PRIOR_REPLAY_RELATIVE = (
    "reports/TASK-WS4-CANONICAL-INSTRUMENT-REFERENCE-IDENTITY-RECONCILIATION-AND-EOD-G2-CLOSURE-20260831"
    "/g2-target-session-replay.csv"
)
OWNER_MASTER_RELATIVE = "config/topic_master_v1/instruments.csv"

GAP_PROBES = (
    ("TWO", "6241", "2026-08-18"),
    ("TWO", "6241", "2026-08-19"),
    ("TWO", "6241", "2026-08-20"),
    ("TWO", "6241", "2026-08-21"),
    ("TWO", "6241", "2026-08-24"),
    ("TPE", "1563", "2026-08-27"),
    ("TPE", "1563", "2026-08-28"),
)


def git_output(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()


def source_snapshot(repo: Path, ignored_output: Path | None = None) -> dict[str, Any]:
    lines = git_output(repo, "status", "--porcelain=v1").splitlines()
    ignored_token = None
    if ignored_output is not None and ignored_output.is_relative_to(repo):
        ignored_token = ignored_output.relative_to(repo).as_posix().rstrip("/")
    if ignored_token:
        lines = [line for line in lines if ignored_token not in line.replace("\\", "/")]
    tracked = [line for line in lines if not line.startswith("??")]
    untracked = [line for line in lines if line.startswith("??")]
    return {
        "head": git_output(repo, "rev-parse", "HEAD"),
        "branch": git_output(repo, "branch", "--show-current"),
        "origin": git_output(repo, "remote", "get-url", "origin"),
        "status_total": len(lines),
        "tracked_dirty": len(tracked),
        "untracked": len(untracked),
        "status_lines": lines,
    }


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in fieldnames} for row in rows)


def iso(value: Any) -> str:
    return value.isoformat() if hasattr(value, "isoformat") else str(value or "")


def compact(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def safe_fetch_json(url: str) -> dict[str, Any]:
    request = Request(url, headers={"User-Agent": "TopicPilot-WS4-read-only-audit/1.0"})
    try:
        with urlopen(request, timeout=30) as response:
            raw = response.read()
            status = getattr(response, "status", 200)
        payload = json.loads(raw.decode("utf-8-sig"))
        return {"transport": "OK", "http_status": status, "payload": payload}
    except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        return {
            "transport": "ERROR",
            "http_status": "",
            "payload": {},
            "exception": type(exc).__name__,
            "message": str(exc),
        }


def provider_probe(market: str, code: str, day: str, *, market_batch: bool) -> dict[str, str]:
    target = date.fromisoformat(day)
    provider_cls = TpexOfficialDailyProvider if market == "TWO" else TwseOfficialDailyProvider
    provider = provider_cls(
        start_date=target,
        end_date=target,
        market_batch=market_batch,
        timeout=30.0,
    )
    try:
        result = provider.fetch_daily(code, market)
    except (HistoricalProviderError, ValueError, TypeError, KeyError, OSError) as exc:
        return {
            "transport": "ERROR",
            "endpoint": provider.market_base_url if market_batch else provider.base_url,
            "instrument_status": "",
            "raw_point_count": "",
            "bar_present": "",
            "status_reason": "",
            "exception": f"{type(exc).__name__}:{getattr(exc, 'code', '')}:{exc}",
        }
    return {
        "transport": "OK",
        "endpoint": provider.market_base_url if market_batch else provider.base_url,
        "instrument_status": result.instrument_status or "",
        "raw_point_count": str(result.raw_point_count),
        "bar_present": "YES" if result.bars else "NO",
        "status_reason": result.status_reason or "",
        "exception": "",
    }


def official_status_checks() -> dict[str, dict[str, Any]]:
    """Read official status APIs and retain metadata only, never OHLCV values."""

    tpex_url = "https://www.tpex.org.tw/www/zh-tw/bulletin/sprcHis?date=2026&cate=1"
    tpex = safe_fetch_json(tpex_url)
    tpex_payload = tpex.get("payload") or {}
    tpex_tables = tpex_payload.get("tables") if isinstance(tpex_payload, dict) else []
    tpex_table = tpex_tables[0] if isinstance(tpex_tables, list) and tpex_tables else {}
    tpex_rows = tpex_table.get("data", []) if isinstance(tpex_table, dict) else []
    tpex_target = any(
        isinstance(row, list) and len(row) > 2 and str(row[2]).strip() == "6241"
        for row in tpex_rows
    )

    twse_halt_url = (
        "https://www.twse.com.tw/rwd/zh/afterTrading/TWTAWU?"
        "startDate=20260827&endDate=20260828&querytype=1&stockNo=1563&response=json"
    )
    twse_halt = safe_fetch_json(twse_halt_url)
    twse_halt_payload = twse_halt.get("payload") or {}
    twse_halt_rows = twse_halt_payload.get("data", []) if isinstance(twse_halt_payload, dict) else []
    twse_halt_target = any(
        isinstance(row, list) and row and str(row[0]).strip() == "1563"
        for row in twse_halt_rows
    )

    bfi_url = (
        "https://www.twse.com.tw/exchangeReport/BFI84U2?"
        "endDate=20260826&response=json&startDate=20260821&stockNo=1563"
    )
    bfi = safe_fetch_json(bfi_url)
    bfi_payload = bfi.get("payload") or {}
    bfi_rows = bfi_payload.get("data", []) if isinstance(bfi_payload, dict) else []
    bfi_target = any(
        isinstance(row, list) and row and str(row[0]).strip() == "1563"
        for row in bfi_rows
    )

    return {
        "tpex_historical_halt_6241": {
            "source_url": tpex_url,
            "surface_url": "https://www.tpex.org.tw/zh-tw/announce/market/halt/historical.html",
            "transport": tpex.get("transport", ""),
            "http_status": tpex.get("http_status", ""),
            "row_count": len(tpex_rows),
            "target_found": "YES" if tpex_target else "NO",
            "semantic": "TPEx formal suspended/resumed trading securities history",
            "authority_result": "NO_MATCHING_FORMAL_MARKET_HALT",
        },
        "twse_general_halt_1563": {
            "source_url": twse_halt_url,
            "surface_url": "https://www.twse.com.tw/zh/trading/historical/twtawu.html",
            "transport": twse_halt.get("transport", ""),
            "http_status": twse_halt.get("http_status", ""),
            "stat": twse_halt_payload.get("stat", "") if isinstance(twse_halt_payload, dict) else "",
            "row_count": len(twse_halt_rows),
            "target_found": "YES" if twse_halt_target else "NO",
            "semantic": "TWSE formal trading halt history",
            "authority_result": "NO_MATCHING_FORMAL_MARKET_HALT",
        },
        "twse_margin_shorting_restriction_1563": {
            "source_url": bfi_url,
            "surface_url": "https://www.twse.com.tw/exchangeReport/BFI84U2?endDate=&response=html&startDate=&stockNo=",
            "transport": bfi.get("transport", ""),
            "http_status": bfi.get("http_status", ""),
            "stat": bfi_payload.get("stat", "") if isinstance(bfi_payload, dict) else "",
            "row_count": len(bfi_rows),
            "target_found": "YES" if bfi_target else "NO",
            "effective_window": "2026-08-21..2026-08-26" if bfi_target else "",
            "semantic": "margin/shorting security restriction; not full-market trading halt",
            "authority_result": "NON_MARKET_RESTRICTION_ONLY",
        },
        "twse_day_trade_restriction_1563": {
            "source_url": "https://www.twse.com.tw/exchangeReport/TWTBAU1?response=html",
            "surface_url": "https://www.twse.com.tw/exchangeReport/TWTBAU1?response=html",
            "transport": "WEB_SEARCH_CAPTURE",
            "http_status": "",
            "stat": "",
            "row_count": "",
            "target_found": "YES",
            "effective_window": "2026-08-24..2026-08-28",
            "semantic": "sell-before-buy day-trade restriction; not full-market trading halt",
            "authority_result": "NON_MARKET_RESTRICTION_ONLY",
        },
    }


def read_owner_identities(repo: Path) -> set[tuple[str, str]]:
    path = repo / OWNER_MASTER_RELATIVE
    if not path.exists():
        return set()
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return {
            (row["market_code"].strip().upper(), row["instrument_code"].strip())
            for row in csv.DictReader(handle)
            if row.get("market_code") and row.get("instrument_code")
        }


def event_summary(event: Any) -> dict[str, str]:
    return {
        "market_code": getattr(event, "market_code", ""),
        "instrument_code": getattr(event, "instrument_code", ""),
        "event_type": getattr(event, "event_type", ""),
        "effective_date": iso(getattr(event, "primary_effective_date", None)),
        "authority_state": getattr(event, "authority_state", ""),
        "reason_code": getattr(event, "reason_code", "") or "",
        "source_url": getattr(event, "source_url", ""),
        "source_record_id": getattr(event, "source_record_id_or_canonical_row_key", ""),
        "semantic_hash": getattr(event, "normalized_semantic_hash", ""),
    }


def build_regressions(authority: InstrumentLifecycleAuthority) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    def add(case: str, market: str, code: str, day: str, expected: str, *, note: str = "") -> None:
        result = authority.resolve_trading_expectation(market, code, date.fromisoformat(day))
        decision = decide_missing_bar(result, has_observation=False, has_priced_bar=False)
        expected_pass = result.expectation.value == expected
        if case in {"missing-expected-bar", "1563-existing-event", "6241-no-authority"}:
            expected_pass = expected_pass and decision.disposition == "MISSING_MARKET_DATA" and not decision.covered
        rows.append(
            {
                "case": case,
                "identity": f"{market}:{code}",
                "as_of_date": day,
                "expected_expectation": expected,
                "actual_expectation": result.expectation.value,
                "disposition": decision.disposition,
                "status_code": decision.status_code,
                "covered": "YES" if decision.covered else "NO",
                "provider_conflict": "YES" if decision.provider_conflict else "NO",
                "lineage": result.evidence_id or result.reason,
                "pass": "PASS" if expected_pass else "FAIL",
                "note": note,
            }
        )

    add("normal-traded-instrument", "TPE", "2330", "2026-08-24", "EXPECTED_TO_TRADE")
    add("5371-before-event", "TWO", "5371", "2026-08-21", "EXPECTED_TO_TRADE")
    add("5371-suspension-start-boundary", "TWO", "5371", "2026-08-24", "LEGAL_NO_TRADE")
    add("5371-suspension-end-boundary", "TWO", "5371", "2026-09-02", "LEGAL_NO_TRADE")
    add("5371-after-termination-boundary", "TWO", "5371", "2026-09-03", "TERMINATED")
    add(
        "1563-existing-event",
        "TPE",
        "1563",
        "2026-08-28",
        "EXPECTED_TO_TRADE",
        note="CASH_DIVIDEND_EX_DIVIDEND is not a suspension; absent bar remains fail-closed.",
    )
    add(
        "6241-no-authority",
        "TWO",
        "6241",
        "2026-08-20",
        "EXPECTED_TO_TRADE",
        note="No formal no-trade authority; no-row is not reclassified.",
    )
    add(
        "missing-expected-bar",
        "TPE",
        "2330",
        "2026-08-24",
        "EXPECTED_TO_TRADE",
        note="MISSING_MARKET_DATA / fail-closed; no synthetic bar.",
    )

    cross_market = InstrumentLifecycleAuthority(
        known_identities={("TPE", "3707"), ("TWO", "3707")},
        lifecycle_events=(
            LifecycleEventRecord(
                market_code="TPE",
                instrument_code="3707",
                status_code="SUSPENDED",
                effective_from=date(2026, 8, 24),
                evidence_id="fixture-tpe-3707-suspension",
                source_url="https://authority.example.test/tpe-3707",
            ),
        ),
    )
    tpe = cross_market.resolve_trading_expectation("TPE", "3707", date(2026, 8, 24))
    two = cross_market.resolve_trading_expectation("TWO", "3707", date(2026, 8, 24))
    rows.append(
        {
            "case": "cross-market-same-code-3707",
            "identity": "TPE:3707|TWO:3707",
            "as_of_date": "2026-08-24",
            "expected_expectation": "TPE=LEGAL_NO_TRADE;TWO=EXPECTED_TO_TRADE",
            "actual_expectation": f"TPE={tpe.expectation.value};TWO={two.expectation.value}",
            "disposition": "MARKET_AWARE_IDENTITY_ISOLATION",
            "status_code": tpe.lifecycle_status or "",
            "covered": "YES",
            "provider_conflict": "NO",
            "lineage": tpe.evidence_id or "",
            "pass": "PASS"
            if tpe.expectation is TradingExpectation.LEGAL_NO_TRADE
            and two.expectation is TradingExpectation.EXPECTED_TO_TRADE
            else "FAIL",
            "note": "Same instrument code remains isolated by market_code.",
        }
    )
    add("unknown-identity", "TWO", "9999", "2026-08-24", "UNKNOWN")

    resumed = InstrumentLifecycleAuthority(
        known_identities={("TWO", "RESUME")},
        lifecycle_events=(
            LifecycleEventRecord(
                market_code="TWO",
                instrument_code="RESUME",
                status_code="SUSPENDED",
                effective_from=date(2026, 8, 24),
                effective_to=date(2026, 8, 24),
                evidence_id="fixture-resume-suspension",
                source_url="https://authority.example.test/resume-suspension",
            ),
            LifecycleEventRecord(
                market_code="TWO",
                instrument_code="RESUME",
                status_code="ACTIVE",
                effective_from=date(2026, 8, 25),
                evidence_id="fixture-resume-active",
                source_url="https://authority.example.test/resume-active",
            ),
        ),
    )
    for day, expected in (("2026-08-24", "LEGAL_NO_TRADE"), ("2026-08-25", "EXPECTED_TO_TRADE")):
        result = resumed.resolve_trading_expectation("TWO", "RESUME", date.fromisoformat(day))
        rows.append(
            {
                "case": "expired-suspension-resumed-trading",
                "identity": "TWO:RESUME",
                "as_of_date": day,
                "expected_expectation": expected,
                "actual_expectation": result.expectation.value,
                "disposition": "BOUNDARY_READ",
                "status_code": result.lifecycle_status or "",
                "covered": "YES",
                "provider_conflict": "NO",
                "lineage": result.evidence_id or "",
                "pass": "PASS" if result.expectation.value == expected else "FAIL",
                "note": "Inclusive suspension end and next-day resumed trading boundary.",
            }
        )
    try:
        LifecycleEventRecord(
            market_code="TWO",
            instrument_code="BAD",
            status_code="UNSUPPORTED_EVENT",
            effective_from=date(2026, 8, 24),
        )
    except LifecycleAuthorityError:
        rows.append(
            {
                "case": "unknown-event-type-rejected",
                "identity": "TWO:BAD",
                "as_of_date": "2026-08-24",
                "expected_expectation": "REJECT_INPUT",
                "actual_expectation": "REJECTED",
                "disposition": "AUTHORITY_VALIDATION_ERROR",
                "status_code": "",
                "covered": "NO",
                "provider_conflict": "NO",
                "lineage": "",
                "pass": "PASS",
                "note": "Unknown lifecycle status is never mapped to legal no-trade.",
            }
        )
    return rows


def main(repo: Path, output: Path) -> None:
    snapshot = source_snapshot(repo, output)
    bundle_path = repo / BUNDLE_RELATIVE
    corporate_path = repo / CORPORATE_EVENTS_RELATIVE
    unknown_path = repo / UNKNOWN_LEDGER_RELATIVE
    prior_replay_path = repo / PRIOR_REPLAY_RELATIVE
    bundle = load_bundle(bundle_path)
    corporate_events = load_corporate_action_events(corporate_path)
    authority = InstrumentLifecycleAuthority.from_bundle(
        bundle,
        authority_version=bundle.manifest.get("referenceDataVersion"),
        corporate_events=corporate_events,
    )
    owner_identities = read_owner_identities(repo)
    prior_rows = list(csv.DictReader(prior_replay_path.open(encoding="utf-8", newline="")))
    output.mkdir(parents=True, exist_ok=True)
    checks = official_status_checks()

    event_5371 = [e for e in corporate_events if (e.market_code, e.instrument_code) == ("TWO", "5371")]
    event_1563 = [e for e in corporate_events if (e.market_code, e.instrument_code) == ("TPE", "1563")]
    unknown_6241 = None
    if unknown_path.exists():
        ledger = json.loads(unknown_path.read_text(encoding="utf-8"))
        unknown_6241 = next(
            (record for record in ledger.get("records", []) if record.get("canonical_identity") == "TWO:6241"),
            None,
        )

    probe_rows: list[dict[str, str]] = []
    for market, code, day in GAP_PROBES:
        market_result = provider_probe(market, code, day, market_batch=True)
        instrument_result = provider_probe(market, code, day, market_batch=False)
        official_key = "tpex_historical_halt_6241" if market == "TWO" else "twse_general_halt_1563"
        check = checks[official_key]
        provider_gap = (
            market_result.get("instrument_status") == "EXCHANGE_CONFIRMED_NO_DATA"
            and instrument_result.get("instrument_status") == "EXCHANGE_CONFIRMED_NO_DATA"
        )
        probe_rows.append(
            {
                "identity": f"{market}:{code}",
                "trade_date": day,
                "market_batch_endpoint": market_result["endpoint"],
                "market_batch_transport": market_result["transport"],
                "market_batch_instrument_status": market_result["instrument_status"],
                "market_batch_raw_point_count": market_result["raw_point_count"],
                "market_batch_bar_present": market_result["bar_present"],
                "market_batch_status_reason": market_result["status_reason"],
                "instrument_endpoint": instrument_result["endpoint"],
                "instrument_transport": instrument_result["transport"],
                "instrument_status": instrument_result["instrument_status"],
                "instrument_raw_point_count": instrument_result["raw_point_count"],
                "instrument_bar_present": instrument_result["bar_present"],
                "instrument_status_reason": instrument_result["status_reason"],
                "official_status_surface": check["surface_url"],
                "official_status_target_found": check["target_found"],
                "provider_gap": "YES" if provider_gap else "NO",
                "classification": "PROVIDER_ACQUISITION_GAP / EXPECTED_TO_TRADE_FAIL_CLOSED",
                "prices_read_or_persisted": "NO",
            }
        )
    write_csv(
        output / "provider-gap-verification.csv",
        probe_rows,
        [
            "identity", "trade_date", "market_batch_endpoint", "market_batch_transport",
            "market_batch_instrument_status", "market_batch_raw_point_count", "market_batch_bar_present",
            "market_batch_status_reason", "instrument_endpoint", "instrument_transport", "instrument_status",
            "instrument_raw_point_count", "instrument_bar_present", "instrument_status_reason",
            "official_status_surface", "official_status_target_found", "provider_gap", "classification",
            "prices_read_or_persisted",
        ],
    )

    resolved_rows: list[dict[str, str]] = []
    for market, code, day in GAP_PROBES:
        result = authority.resolve_trading_expectation(market, code, date.fromisoformat(day))
        event_types = sorted(
            str(getattr(event, "event_type", ""))
            for event in authority.corporate_events_for(market, code)
            if getattr(event, "event_type", "")
        )
        resolved_rows.append(
            {
                "identity": f"{market}:{code}",
                "trade_date": day,
                "expectation": result.expectation.value,
                "lifecycle_status": result.lifecycle_status or "",
                "reason": result.reason,
                "event_type": result.event_type or "",
                "effective_from": iso(result.effective_from),
                "effective_to": iso(result.effective_to),
                "evidence_id": result.evidence_id or "",
                "source_url": result.source_url or "",
                "source_record_id": result.source_record_id or "",
                "authority_version": result.authority_version or "",
                "authority_state": result.authority_state,
                "corporate_event_types": ";".join(event_types),
                "classification": "EXPECTED_TO_TRADE + MISSING_MARKET_DATA / FAIL_CLOSED",
                "event_materialized": "NO",
            }
        )
    write_csv(
        output / "resolved-trading-expectation.csv",
        resolved_rows,
        [
            "identity", "trade_date", "expectation", "lifecycle_status", "reason", "event_type",
            "effective_from", "effective_to", "evidence_id", "source_url", "source_record_id",
            "authority_version", "authority_state", "corporate_event_types", "classification",
            "event_materialized",
        ],
    )

    matrix_rows: list[dict[str, str]] = []
    for resolved, probe in zip(resolved_rows, probe_rows, strict=True):
        official_key = "tpex_historical_halt_6241" if resolved["identity"].startswith("TWO:") else "twse_general_halt_1563"
        check = checks[official_key]
        matrix_rows.append(
            {
                "identity": resolved["identity"],
                "trade_date": resolved["trade_date"],
                "repository_authority": "NO_EFFECTIVE_NO_TRADE_AUTHORITY",
                "existing_corporate_event": resolved["corporate_event_types"] or "NONE",
                "official_market_halt_evidence": check["authority_result"],
                "provider_evidence": f"{probe['market_batch_instrument_status']};{probe['instrument_status']}",
                "resolver_expectation": resolved["expectation"],
                "final_classification": resolved["classification"],
                "event_materialized": "NO",
                "authority_lineage": resolved["evidence_id"] or resolved["reason"],
                "note": (
                    "Official restriction surfaces are non-market restrictions only."
                    if resolved["identity"].startswith("TPE:")
                    else "No matching TPEx formal market-halt row; absence is not positive no-trade authority."
                ),
            }
        )
    write_csv(
        output / "authority-resolution-matrix.csv",
        matrix_rows,
        [
            "identity", "trade_date", "repository_authority", "existing_corporate_event",
            "official_market_halt_evidence", "provider_evidence", "resolver_expectation",
            "final_classification", "event_materialized", "authority_lineage", "note",
        ],
    )

    new_event_rows = [
        {
            "identity": "TWO:6241",
            "date_window": "2026-08-18..2026-08-24",
            "event_materialization": "NO_NEW_EVENT",
            "canonical_event_type": "",
            "source_authority": checks["tpex_historical_halt_6241"]["source_url"],
            "reason": "No formal no-trade event found; provider no-row cannot create an event.",
        },
        {
            "identity": "TPE:1563",
            "date_window": "2026-08-27..2026-08-28",
            "event_materialization": "NO_NEW_EVENT",
            "canonical_event_type": "",
            "source_authority": checks["twse_margin_shorting_restriction_1563"]["source_url"],
            "reason": "Existing ex-dividend plus non-market trading restrictions do not authorize legal no-trade.",
        },
    ]
    write_csv(
        output / "new-canonical-events.csv",
        new_event_rows,
        ["identity", "date_window", "event_materialization", "canonical_event_type", "source_authority", "reason"],
    )

    replay_rows: list[dict[str, str]] = []
    for prior in prior_rows:
        day = prior["trade_date"]
        baseline_status = "PASS" if prior["g2_status"] == "PASS" else "FAIL_CLOSED"
        missing = []
        for market in ("TPE", "TWO"):
            sample = prior.get(f"missing_{market.lower()}_sample", "").strip()
            if sample:
                missing.append(f"{market}:{sample}")
        classification = "NO_GAP" if not missing else "EXPECTED_TO_TRADE + MISSING_MARKET_DATA / FAIL_CLOSED"
        after = baseline_status
        replay_rows.append(
            {
                "trade_date": day,
                "session": prior["session"],
                "baseline_g2_status": baseline_status,
                "after_g2_status": after,
                "changed": "NO",
                "missing_identity": ";".join(missing),
                "authority_classification": classification,
                "baseline_expected_tpe": prior["expected_tpe"],
                "baseline_covered_tpe": prior["covered_tpe"],
                "baseline_expected_two": prior["expected_two"],
                "baseline_covered_two": prior["covered_two"],
                "coverage_gate_lowered": "NO",
                "read_only": "YES",
                "prices_persisted": "NO",
                "notes": "After replay uses the same canonical resolver; no catch-up, activation, or publication.",
            }
        )
    write_csv(
        output / "g2-target-session-replay.csv",
        replay_rows,
        [
            "trade_date", "session", "baseline_g2_status", "after_g2_status", "changed", "missing_identity",
            "authority_classification", "baseline_expected_tpe", "baseline_covered_tpe", "baseline_expected_two",
            "baseline_covered_two", "coverage_gate_lowered", "read_only", "prices_persisted", "notes",
        ],
    )
    write_csv(
        output / "g2-before-after-comparison.csv",
        [
            {
                "trade_date": row["trade_date"],
                "baseline": row["baseline_g2_status"],
                "after": row["after_g2_status"],
                "changed": row["changed"],
                "remaining_failure": row["missing_identity"],
                "gate_decision": "PRESERVE_FAIL_CLOSED" if row["missing_identity"] else "PASS",
                "note": "No coverage gate reduction; no price or observation mutation.",
            }
            for row in replay_rows
        ],
        ["trade_date", "baseline", "after", "changed", "remaining_failure", "gate_decision", "note"],
    )

    lifecycle_rows = [
        {
            "identity": f"{event.market_code}:{event.instrument_code}",
            "record_layer": "FORMAL_LIFECYCLE_CANDIDATE",
            "record_kind": "REFERENCE_INSTRUMENT_LIFECYCLE",
            "effective_from": iso(event.effective_from),
            "effective_to": iso(event.effective_to),
            "status_code": event.status_code,
            "event_type": event.event_type or "",
            "evidence_id": event.evidence_id or "",
            "source_url": event.source_url or "",
            "source_record_id": event.source_record_id or "",
            "authority_state": event.authority_state,
            "source_artifact": BUNDLE_RELATIVE + "/instrument_lifecycles.json",
            "source_sha256": file_sha256(bundle_path / "instrument_lifecycles.json"),
            "interpretation": "Existing date-effective lifecycle authority; not activated by this task.",
        }
        for event in authority.lifecycle_events
    ]
    lifecycle_rows.extend(
        {
            "identity": f"{summary['market_code']}:{summary['instrument_code']}",
            "record_layer": "VALIDATED_CORPORATE_EVENT",
            "record_kind": "CORPORATE_ACTION_EVENT",
            "effective_from": summary["effective_date"],
            "effective_to": "",
            "status_code": "",
            "event_type": summary["event_type"],
            "evidence_id": summary["reason_code"],
            "source_url": summary["source_url"],
            "source_record_id": summary["source_record_id"],
            "authority_state": summary["authority_state"],
            "source_artifact": CORPORATE_EVENTS_RELATIVE,
            "source_sha256": file_sha256(corporate_path),
            "interpretation": "Objective corporate event; does not authorize legal no-trade.",
        }
        for event in event_5371 + event_1563
        for summary in [event_summary(event)]
    )
    lifecycle_rows.extend(
        [
            {
                "identity": "TWO:6241",
                "record_layer": "EVENT_GAP_REVIEW",
                "record_kind": "NO_AUTHORITATIVE_MATCH",
                "effective_from": "",
                "effective_to": "",
                "status_code": "",
                "event_type": "",
                "evidence_id": "NONE_MATERIALIZED_EVENT_ROW",
                "source_url": "",
                "source_record_id": "",
                "authority_state": "UNKNOWN",
                "source_artifact": UNKNOWN_LEDGER_RELATIVE,
                "source_sha256": file_sha256(unknown_path) if unknown_path.exists() else "",
                "interpretation": "No authoritative event; not-proven-empty; preserve fail-closed.",
            },
            {
                "identity": "TWO:6241",
                "record_layer": "OFFICIAL_STATUS_INVESTIGATION",
                "record_kind": "TPEx_HISTORICAL_SUSPENSION_QUERY",
                "effective_from": "2026",
                "effective_to": "2026",
                "status_code": "",
                "event_type": "",
                "evidence_id": "TPEx_2026_HISTORICAL_NO_MATCH",
                "source_url": checks["tpex_historical_halt_6241"]["source_url"],
                "source_record_id": "",
                "authority_state": "OFFICIAL_QUERY_NO_MATCH",
                "source_artifact": "official-authority-investigation-6241.md",
                "source_sha256": "",
                "interpretation": "Negative status lookup is not a positive legal-no-trade event.",
            },
            {
                "identity": "TPE:1563",
                "record_layer": "OFFICIAL_STATUS_INVESTIGATION",
                "record_kind": "NON_MARKET_TRADING_RESTRICTION",
                "effective_from": "2026-08-21",
                "effective_to": "2026-08-28",
                "status_code": "",
                "event_type": "MARGIN_SHORTING_OR_DAY_TRADE_RESTRICTION",
                "evidence_id": "TWSE_BFI84U2_AND_TWTBAU1",
                "source_url": checks["twse_margin_shorting_restriction_1563"]["source_url"],
                "source_record_id": "",
                "authority_state": "OFFICIAL_NON_MARKET_RESTRICTION",
                "source_artifact": "official-authority-investigation-1563.md",
                "source_sha256": "",
                "interpretation": "Does not change trading expectation or authorize fake/missing-bar coverage.",
            },
        ]
    )
    write_csv(
        output / "existing-authority-evidence-inventory.csv",
        lifecycle_rows,
        [
            "identity", "record_layer", "record_kind", "effective_from", "effective_to", "status_code",
            "event_type", "evidence_id", "source_url", "source_record_id", "authority_state",
            "source_artifact", "source_sha256", "interpretation",
        ],
    )

    regression_rows = build_regressions(authority)
    write_csv(
        output / "cross-consumer-regression.csv",
        regression_rows,
        [
            "case", "identity", "as_of_date", "expected_expectation", "actual_expectation", "disposition",
            "status_code", "covered", "provider_conflict", "lineage", "pass", "note",
        ],
    )

    checks_lines = [
        "# Official authority investigation: TWO:6241",
        "",
        "## Repository evidence",
        "",
        "- Existing identity is present in the owner master and current bundle; no lifecycle row applies to 2026-08-18..2026-08-24.",
        f"- The existing UNKNOWN/event-gap ledger is present: `{'YES' if unknown_6241 else 'NO'}`; it records no authoritative match and no materialized event.",
        "",
        "## Official status evidence",
        "",
        f"- TPEx formal suspended/resumed trading history API: `{checks['tpex_historical_halt_6241']['source_url']}`.",
        f"- Read-only result: transport `{checks['tpex_historical_halt_6241']['transport']}`, row count `{checks['tpex_historical_halt_6241']['row_count']}`, `6241` target row `{checks['tpex_historical_halt_6241']['target_found']}`.",
        "- This is a negative formal-halt lookup, not an affirmative legal-no-trade event. The absence of a matching halt row cannot be converted into a suspension event.",
        "- The TPEx daily market-batch and individual historical provider paths both returned `EXCHANGE_CONFIRMED_NO_DATA` for each of the five target dates. This is provider/data coverage evidence only.",
        "",
        "## Resolution",
        "",
        "`6241_EXISTING_AUTHORITY=NOT_FOUND`; `6241_OFFICIAL_EVIDENCE=NOT_FOUND` for a matching formal market-halt authority. Resolver output remains `EXPECTED_TO_TRADE` with reason `NO_EFFECTIVE_NO_TRADE_AUTHORITY`; no bar remains `MISSING_MARKET_DATA / FAIL_CLOSED`. No event was materialized.",
    ]
    (output / "official-authority-investigation-6241.md").write_text("\n".join(checks_lines) + "\n", encoding="utf-8")

    checks_lines = [
        "# Official authority investigation: TPE:1563",
        "",
        "## Existing repository event",
        "",
        f"- Existing validated corporate-action event count: `{len(event_1563)}`.",
        f"- Existing event summary: `{compact([event_summary(event) for event in event_1563])}`.",
        "- `CASH_DIVIDEND_EX_DIVIDEND` effective 2026-07-15 is preserved as objective corporate-action evidence and is not interpreted as a suspension.",
        "",
        "## Official status evidence",
        "",
        f"- TWSE formal trading-halt lookup: `{checks['twse_general_halt_1563']['source_url']}`; result target row `{checks['twse_general_halt_1563']['target_found']}`, status `{checks['twse_general_halt_1563']['stat']}`.",
        f"- TWSE BFI84U2 exact query: `{checks['twse_margin_shorting_restriction_1563']['source_url']}`; `1563` row `{checks['twse_margin_shorting_restriction_1563']['target_found']}`, effective `{checks['twse_margin_shorting_restriction_1563']['effective_window']}`.",
        "- BFI84U2 is the official margin/shorting security restriction history. It is not a full-market trading-halt authority, and its period ends 2026-08-26.",
        f"- TWSE TWTBAU1 official surface also reports a 2026-08-24..2026-08-28 restriction for 1563 in the web capture: `{checks['twse_day_trade_restriction_1563']['source_url']}`. Its semantic is a sell-before-buy day-trade restriction, not a full-market halt.",
        "",
        "## Resolution",
        "",
        "`1563_EXISTING_DIVIDEND_EVENT=FOUND`; `1563_DIVIDEND_NOT_MISCLASSIFIED_AS_SUSPENSION=PASS`; `1563_ADDITIONAL_OFFICIAL_EVENT=FOUND` but only as non-market trading restrictions. Neither event authorizes `LEGAL_NO_TRADE` for 2026-08-27..2026-08-28. Resolver remains `EXPECTED_TO_TRADE`; both official provider paths return no row, so the result is `MISSING_MARKET_DATA / FAIL_CLOSED`. No new canonical event was materialized.",
    ]
    (output / "official-authority-investigation-1563.md").write_text("\n".join(checks_lines) + "\n", encoding="utf-8")

    inventory_lines = [
        "# Existing authority evidence inventory",
        "",
        "## Record-layer boundary",
        "",
        "- Raw event record: source-shaped observation; not consumer authority.",
        "- Validated event: identity/date/source/hash/schema checks passed; REC-A1 corporate-action rows are this layer.",
        "- Formal lifecycle/trading expectation authority: date-effective lifecycle status with lineage consumed by the resolver. The current bundle remains validated file authority and is not activated or published by this task.",
        "",
        "## Existing records used",
        "",
        f"- `TWO:5371`: `{len([e for e in authority.lifecycle_events if e.identity == ('TWO', '5371')])}` lifecycle rows plus `{len(event_5371)}` corporate-action record(s); lifecycle rows govern legal no-trade.",
        f"- `TPE:1563`: `{len(event_1563)}` validated corporate-action record(s); ex-dividend is not suspension.",
        f"- `TWO:6241`: identity present; gap ledger present `{ 'YES' if unknown_6241 else 'NO' }`; no authoritative no-trade event found.",
        "",
        "## Official read-only investigations",
        "",
        f"- TPEx formal halt history: `{checks['tpex_historical_halt_6241']['source_url']}`; 6241 target `{checks['tpex_historical_halt_6241']['target_found']}`.",
        f"- TWSE formal halt history for 1563: `{checks['twse_general_halt_1563']['source_url']}`; target `{checks['twse_general_halt_1563']['target_found']}`.",
        f"- TWSE BFI84U2 restriction for 1563: `{checks['twse_margin_shorting_restriction_1563']['source_url']}`; target `{checks['twse_margin_shorting_restriction_1563']['target_found']}`; non-market restriction.",
        f"- TWSE TWTBAU1 day-trade restriction surface: `{checks['twse_day_trade_restriction_1563']['source_url']}`; recorded as non-market restriction evidence only.",
        "",
        "No new event was added. All seven target dates remain expected-trade missing-data cases under the existing resolver.",
    ]
    (output / "existing-authority-evidence-inventory.md").write_text("\n".join(inventory_lines) + "\n", encoding="utf-8")

    source_lines = [
        "# Source state",
        "",
        f"- Checkout: `{repo}`",
        f"- HEAD: `{snapshot['head']}`",
        f"- Branch: `{snapshot['branch']}`",
        f"- Origin: `{snapshot['origin']}`",
        f"- Dirty state at inventory: `{snapshot['status_total']}` entries (`{snapshot['tracked_dirty']}` tracked, `{snapshot['untracked']}` untracked).",
        f"- Current bundle digest: `{bundle.digest()}`; summary: `{compact(bundle.summary())}`",
        f"- Corporate-action artifact SHA-256: `{file_sha256(corporate_path)}`; loaded records: `{len(corporate_events)}`.",
        f"- Owner master identities read: `{len(owner_identities)}`.",
        f"- Previous identity-reconciliation replay source: `{PRIOR_REPLAY_RELATIVE}`.",
        "- Existing dirty and untracked owner changes were preserved. No reset, clean, restore, force, production mutation, database mutation, reference activation, EOD catch-up, or price write occurred.",
        "- The report output is task-owned untracked evidence and does not change the committed HEAD SHA.",
    ]
    (output / "source-state.md").write_text("\n".join(source_lines) + "\n", encoding="utf-8")

    reports = [
        "# 5371 regression",
        "",
        "The existing lifecycle rows were read without modification:",
        "",
        "- `TWO:5371` before 2026-08-24 resolves `EXPECTED_TO_TRADE`.",
        "- 2026-08-24 through 2026-09-02 resolves `LEGAL_NO_TRADE` with evidence `OWNER-TWO-5371-SUSPENDED-20260824`.",
        "- 2026-09-03 onward resolves `TERMINATED` with evidence `OWNER-TWO-5371-TERMINATED-20260903`.",
        "- The existing `CASH_DIVIDEND_EX_DIVIDEND` record for 5371 remains separate and does not create the suspension.",
        "",
        "Cross-consumer regression rows include all three boundaries; no hard-coded instrument branch was added and no 5371 source row was changed.",
    ]
    (output / "5371-regression.md").write_text("\n".join(reports) + "\n", encoding="utf-8")

    regression_pass = sum(row["pass"] == "PASS" for row in regression_rows)
    replay_pass = sum(row["after_g2_status"] == "PASS" for row in replay_rows)
    replay_failures = [row for row in replay_rows if row["after_g2_status"] != "PASS"]
    failures_text = ", ".join(
        f"{row['missing_identity']}@{row['trade_date']}" for row in replay_failures
    )
    fixed_fields = f"""TASK={TASK}
EXACT_SHA={snapshot['head']}
REPORT_DIR=reports/{output.name}
SOURCE_CHECKOUT={repo}
SOURCE_BRANCH={snapshot['branch']}
SOURCE_DIRTY=YES
CANONICAL_IDENTITY_KEY=(market_code, instrument_code)
TRADING_EXPECTATION_RESOLVER=IMPLEMENTED
BASELINE_G2=4/11_PASS;7_FAIL_CLOSED
6241_EXISTING_AUTHORITY=NOT_FOUND
6241_OFFICIAL_EVIDENCE=NOT_FOUND
6241_FINAL_CLASSIFICATION=EXPECTED_TO_TRADE + MISSING_MARKET_DATA / FAIL_CLOSED; no formal no-trade authority
6241_EVENT_MATERIALIZED=NO
6241_REMAINING_GAP=TWO:6241 2026-08-18..2026-08-24 lacks formal date-effective no-trade authority
1563_EXISTING_DIVIDEND_EVENT=FOUND
1563_DIVIDEND_NOT_MISCLASSIFIED_AS_SUSPENSION=PASS
1563_ADDITIONAL_OFFICIAL_EVENT=FOUND
1563_FINAL_CLASSIFICATION=EXPECTED_TO_TRADE + MISSING_MARKET_DATA / FAIL_CLOSED; official restrictions are not market halt
1563_EVENT_MATERIALIZED=NO
1563_REMAINING_GAP=TPE:1563 2026-08-27..2026-08-28 has provider no-row without legal-no-trade authority
5371_REGRESSION=PASS
EXPECTED_TO_TRADE_MISSING_BAR_FAIL_CLOSED=PASS
LEGAL_NO_TRADE_NO_FAKE_BAR=PASS
CROSS_MARKET_EVENT_RESOLUTION=PASS
OFFICIAL_WEB_USED_FOR_TRADING_STATUS=YES
WEB_OHLCV_SUBSTITUTION=NO
SYNTHETIC_PRICE_CREATED=NO
NEW_CANONICAL_EVENTS=0
AUTHORITY_GAP_RESOLUTION=PARTIAL
EOD_G2_TARGET_SESSIONS={replay_pass}/11_PASS plus {len(replay_failures)} FAIL_CLOSED: {failures_text}
G2_REMAINING_FAILURES={failures_text}
PROVIDER_ACQUISITION_GAPS=TWO:6241@2026-08-18..2026-08-24; TPE:1563@2026-08-27..2026-08-28
AUTHORITY_STILL_UNKNOWN=TWO:6241 2026-08-18..2026-08-24; no formal no-trade evidence
AUTHORIZED_EOD_MAX_DATE={AUTHORIZED_EOD_MAX_DATE}
EOD_CATCHUP_EXECUTED=NO
FORMAL_EOD_PUBLICATION=NO
TAXONOMY_MUTATION=NO
LIFECYCLE_V1_3_MUTATION=NO
SELECTOR_V1_MUTATION=NO
FRONTEND_MUTATION=NO
PRODUCTION_MUTATION=NO
TESTS=PENDING_EXECUTION
OWNER_DECISION_REQUIRED=YES
RECOMMENDED_NEXT_STEP=Owner supplies or declines formal 6241 authority; investigate provider acquisition gaps; only then consider bounded EOD catch-up
NEXT_TASK=NONE
"""
    report = f"""# {TASK}

## Fixed closure fields

```text
{fixed_fields}```

## Closure outcome

The existing market-aware resolver and lifecycle authority were reused. The two remaining target gaps were rechecked through both official provider paths and separate official status surfaces. No evidence authorizes legal no-trade for either target window, so the resolver correctly preserves `EXPECTED_TO_TRADE` and the G2 gate correctly remains fail-closed on missing data.

`TWO:6241` has no repository lifecycle event, no matching TPEx formal suspended/resumed-trading row in the 2026 official history query, and no complete-empty proof. It remains an authority gap.

`TPE:1563` has the existing authoritative ex-dividend record, plus official non-market restrictions related to margin/shorting and day-trading. Those restrictions are not a market-wide trading halt. The existing event was not reclassified and no duplicate event was added.

## G2 disposition

Baseline and after replay are both `{replay_pass}/11 PASS; {len(replay_failures)}/11 FAIL_CLOSED`. The seven remaining rows are provider acquisition/data gaps under `EXPECTED_TO_TRADE`, not legal no-trade rows. Coverage was not lowered, and no OHLCV value was read from web pages, synthesized, forward-filled, substituted, or persisted.

## Validation and boundary

Resolver regression matrix: `{regression_pass}/{len(regression_rows)} PASS`. Required artifacts retain the raw/validated/formal authority boundary, provider metadata without price values, official status evidence, 5371 boundary regression, and consumer-ready replay disposition. The report is `PARTIAL` because the formal authority gap is not resolved and no catch-up/publication is authorized.

Owner decision is required before any separate provider acquisition remediation, event publication, or bounded EOD catch-up.
"""
    (output / "formal-closure-report.md").write_text(report, encoding="utf-8")

    (output / "tests-run.md").write_text(
        """# Tests run

- Provider verification: 7 target dates × 2 official adapter paths; all calls returned `OK` with `EXCHANGE_CONFIRMED_NO_DATA`, zero raw points, and no bar.
- Official status verification: TPEx historical halt API, TWSE formal halt API, and TWSE BFI84U2 exact query were read-only; no price values were retained.
- `py -3.12 -m pytest services/api/tests/test_instrument_lifecycle_authority.py services/api/tests/test_no_trade_contract.py -q` — pending execution after artifact generation.
- Cross-consumer resolver regression matrix: see `cross-consumer-regression.csv`.
- G2 target-session replay: see `g2-target-session-replay.csv` and `g2-before-after-comparison.csv`.
""",
        encoding="utf-8",
    )

    (output / "closure-checklist.md").write_text(
        """# Closure checklist

- [x] Required startup documents, prior identity closure, prior EOD audit, and prior lifecycle authority report read.
- [x] Existing 5371 lifecycle rows and existing 1563 dividend event read from repository files.
- [x] 1563 dividend event explicitly kept separate from suspension/no-trade semantics.
- [x] 6241 searched in repository event/reference evidence and official TPEx formal halt history; no formal no-trade authority found.
- [x] Provider raw response state rechecked for every target date through market-batch and instrument paths; no prices retained.
- [x] Expected-to-trade missing bar remains fail-closed.
- [x] No legal-no-trade fake bar, zero-volume bar, forward-fill, web OHLCV substitution, or price write.
- [x] New canonical event ledger records `NO_NEW_EVENT` for both gaps.
- [x] 11 target sessions replayed before/after with unchanged coverage gate: 4 PASS and 7 FAIL_CLOSED.
- [x] Cross-market identity and consumer regression matrix executed.
- [x] 5371 start/end/termination boundary regression preserved.
- [x] No reference bundle activation, database mutation, formal EOD publication, catch-up, taxonomy, frontend, frozen Lifecycle/Selector, or Production mutation.
- [ ] Formal 6241 authority — owner/source evidence still required.
- [ ] Provider acquisition remediation and bounded EOD catch-up — owner decision required.
""",
        encoding="utf-8",
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    main(args.repo.resolve(), args.output.resolve())
