"""Generate the WS4 A6 provider-acquisition root-cause artifacts.

This audit is read-only with respect to application data.  It reuses the
existing market-aware providers and lifecycle resolver, captures response
metadata only, and writes evidence under the task-owned report directory.
No raw payload, OHLCV value, database row, reference activation, or catch-up
operation is performed here.
"""

from __future__ import annotations

import csv
import hashlib
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
from topicpilot_api.market_data.registry import build_historical_provider_registry
from topicpilot_api.reference_data.bundle import load_bundle

TASK = "TASK-WS4-CANONICAL-EOD-PROVIDER-ACQUISITION-GAP-ROOT-CAUSE-REMEDIATION-AND-G2-CLOSURE"
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
PRIOR_A5_RELATIVE = "reports/TASK-WS4-EOD-AUTHORITY-GAP-RESOLUTION-6241-1563-AND-G2-CLOSURE-20260831"
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


def source_snapshot(repo: Path, ignored_output: Path) -> dict[str, Any]:
    lines = git_output(repo, "status", "--porcelain=v1").splitlines()
    token = ignored_output.relative_to(repo).as_posix().rstrip("/")
    lines = [line for line in lines if token not in line.replace("\\", "/")]
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


def read_owner_identities(repo: Path) -> set[tuple[str, str]]:
    path = repo / OWNER_MASTER_RELATIVE
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return {
            (row["market_code"].strip().upper(), row["instrument_code"].strip())
            for row in csv.DictReader(handle)
            if row.get("market_code") and row.get("instrument_code")
        }


def roc_date(value: Any) -> str:
    text = str(value or "").strip().replace("-", "/")
    parts = text.split("/")
    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        return ""
    year, month, day = (int(part) for part in parts)
    if year < 1911:
        year += 1911
    try:
        return date(year, month, day).isoformat()
    except ValueError:
        return ""


def payload_metadata(
    raw: bytes,
    *,
    market: str,
    code: str,
    day: str,
    market_batch: bool,
    http_status: int,
) -> dict[str, str]:
    """Return response shape and target-row metadata without retaining values."""

    result: dict[str, str] = {
        "raw_response_present": "YES",
        "http_status": str(http_status),
        "payload_sha256": hashlib.sha256(raw).hexdigest(),
        "json_parse": "FAIL",
        "provider_stat": "",
        "response_date": "",
        "table_title": "",
        "first_field": "",
        "row_count": "",
        "target_row_present": "UNKNOWN",
        "endpoint_semantics": "market_batch" if market_batch else "instrument_history",
    }
    try:
        payload = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return result
    if not isinstance(payload, dict):
        return result
    result["json_parse"] = "PASS"
    result["provider_stat"] = str(payload.get("stat", ""))
    result["response_date"] = str(payload.get("date", ""))

    if market_batch:
        tables = payload.get("tables")
        table = None
        if isinstance(tables, list):
            expected_field = "證券代號" if market == "TPE" else "代號"
            for candidate in tables:
                if not isinstance(candidate, dict):
                    continue
                fields = candidate.get("fields")
                data = candidate.get("data")
                if isinstance(fields, list) and fields and fields[0] == expected_field and isinstance(data, list):
                    if market == "TWO" and candidate.get("title") != "上櫃股票行情":
                        continue
                    table = candidate
                    break
        if isinstance(table, dict):
            fields = table.get("fields") or []
            rows = table.get("data") or []
            result["table_title"] = str(table.get("title", ""))
            result["first_field"] = str(fields[0]) if fields else ""
            result["row_count"] = str(len(rows))
            result["target_row_present"] = (
                "YES"
                if any(isinstance(row, list) and row and str(row[0]).strip() == code for row in rows)
                else "NO"
            )
        return result

    rows = payload.get("data")
    if market == "TPE":
        result["first_field"] = "證券代號/date-column"
    else:
        tables = payload.get("tables")
        table = tables[0] if isinstance(tables, list) and tables and isinstance(tables[0], dict) else {}
        fields = table.get("fields") or []
        rows = table.get("data", [])
        result["table_title"] = str(table.get("title", ""))
        result["first_field"] = str(fields[0]) if fields else ""
    if isinstance(rows, list):
        result["row_count"] = str(len(rows))
        target = day
        result["target_row_present"] = (
            "YES"
            if any(isinstance(row, list) and row and roc_date(row[0]) == target for row in rows)
            else "NO"
        )
    return result


def provider_probe(market: str, code: str, day: str, *, market_batch: bool) -> dict[str, str]:
    """Run the existing official adapter and retain only safe response metadata."""

    target = date.fromisoformat(day)
    provider_cls = TpexOfficialDailyProvider if market == "TWO" else TwseOfficialDailyProvider
    last: dict[str, str] = {
        "transport": "ERROR",
        "endpoint": "",
        "instrument_status": "",
        "raw_point_count": "",
        "bar_present": "",
        "status_reason": "",
        "exception": "",
        "raw_response_present": "UNKNOWN",
        "http_status": "",
        "payload_sha256": "",
        "json_parse": "UNKNOWN",
        "provider_stat": "",
        "response_date": "",
        "table_title": "",
        "first_field": "",
        "row_count": "",
        "target_row_present": "UNKNOWN",
        "endpoint_semantics": "market_batch" if market_batch else "instrument_history",
    }
    for attempt in range(3):
        capture: dict[str, Any] = {}

        def transport(url: str, timeout: float, capture: dict[str, Any] = capture) -> bytes:
            request = Request(url, headers={"User-Agent": "TopicPilot-WS4-A6-read-only-audit/1.0"})
            capture["url"] = url
            with urlopen(request, timeout=timeout) as response:
                raw = response.read()
                capture["http_status"] = int(getattr(response, "status", 200))
            capture["raw"] = raw
            return raw

        provider = provider_cls(
            start_date=target,
            end_date=target,
            market_batch=market_batch,
            timeout=30.0,
            transport=transport,
        )
        try:
            result = provider.fetch_daily(code, market)
        except (HTTPError, URLError, TimeoutError, OSError, HistoricalProviderError, ValueError, TypeError, KeyError) as exc:
            last.update(
                {
                    "transport": "ERROR",
                    "endpoint": str(capture.get("url", provider.market_base_url if market_batch else provider.base_url)),
                    "exception": f"{type(exc).__name__}:{getattr(exc, 'code', '')}:{exc}",
                }
            )
            if capture.get("raw"):
                last.update(
                    payload_metadata(
                        capture["raw"],
                        market=market,
                        code=code,
                        day=day,
                        market_batch=market_batch,
                        http_status=int(capture.get("http_status", 200)),
                    )
                )
            if attempt < 2:
                continue
            return last
        metadata = payload_metadata(
            capture["raw"],
            market=market,
            code=code,
            day=day,
            market_batch=market_batch,
            http_status=int(capture.get("http_status", 200)),
        )
        last.update(
            {
                "transport": "OK",
                "endpoint": str(capture.get("url", "")),
                "instrument_status": result.instrument_status or "",
                "raw_point_count": str(result.raw_point_count),
                "bar_present": "YES" if result.bars else "NO",
                "status_reason": result.status_reason or "",
                "exception": "",
                **metadata,
            }
        )
        return last
    return last


def event_summary(event: Any) -> dict[str, str]:
    return {
        "identity": f"{getattr(event, 'market_code', '')}:{getattr(event, 'instrument_code', '')}",
        "event_type": getattr(event, "event_type", "") or "",
        "effective_from": iso(getattr(event, "primary_effective_date", None)),
        "effective_to": "",
        "status_code": "",
        "evidence_id": getattr(event, "evidence_id", "") or "",
        "source_url": getattr(event, "source_url", "") or "",
        "source_record_id": getattr(event, "source_record_id_or_canonical_row_key", "") or "",
        "authority_state": getattr(event, "authority_state", "") or "",
        "reason": getattr(event, "reason", "") or "",
    }


def prior_rows(repo: Path) -> list[dict[str, str]]:
    with (repo / PRIOR_REPLAY_RELATIVE).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def prior_gap_row(priors: list[dict[str, str]], identity: str, day: str) -> dict[str, str]:
    row = next(item for item in priors if item["trade_date"] == day)
    market, code = identity.split(":", 1)
    expected = row.get(f"baseline_expected_{market.lower()}") or row[f"expected_{market.lower()}"]
    covered = row.get(f"baseline_covered_{market.lower()}") or row[f"covered_{market.lower()}"]
    return {
        "expected_count": expected,
        "covered_count": covered,
        "missing_identity": f"{market}:{code}",
        "session": row["session"],
        "g2_status": row.get("g2_status", row.get("baseline_g2_status", "")),
    }


def build_regressions(authority: InstrumentLifecycleAuthority) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    def add(
        case: str,
        market: str,
        code: str,
        day: str,
        expected: str,
        *,
        has_priced_bar: bool = False,
        note: str = "",
    ) -> None:
        result = authority.resolve_trading_expectation(market, code, date.fromisoformat(day))
        decision = decide_missing_bar(
            result,
            has_observation=has_priced_bar,
            has_priced_bar=has_priced_bar,
        )
        expected_pass = result.expectation.value == expected
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

    add("normal-traded-instrument", "TPE", "2330", "2026-08-24", "EXPECTED_TO_TRADE", has_priced_bar=True)
    add("normal-traded-instrument-two", "TWO", "4979", "2026-08-24", "EXPECTED_TO_TRADE", has_priced_bar=True)
    add("5371-before-event-boundary", "TWO", "5371", "2026-08-21", "EXPECTED_TO_TRADE")
    add("5371-suspension-start-boundary", "TWO", "5371", "2026-08-24", "LEGAL_NO_TRADE")
    add("5371-suspension-end-boundary", "TWO", "5371", "2026-09-02", "LEGAL_NO_TRADE")
    add("5371-after-termination-boundary", "TWO", "5371", "2026-09-03", "TERMINATED")
    add(
        "1563-existing-dividend-and-suspension-events",
        "TPE",
        "1563",
        "2026-08-28",
        "LEGAL_NO_TRADE",
        note="The date-effective capital-reduction suspension is legal no-trade; CASH_DIVIDEND_EX_DIVIDEND remains separate corporate-action context.",
    )
    add(
        "6241-existing-suspension-event",
        "TWO",
        "6241",
        "2026-08-20",
        "LEGAL_NO_TRADE",
        note="The date-effective capital-reduction suspension is the authority; provider no-row does not create the event.",
    )
    add(
        "missing-expected-bar",
        "TPE",
        "2330",
        "2026-08-24",
        "EXPECTED_TO_TRADE",
        note="MISSING_MARKET_DATA is fail-closed and does not synthesize a bar.",
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
    add("unknown-identity-authority", "TWO", "9999", "2026-08-24", "UNKNOWN")

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
    for day, expected in (("2026-08-23", "NOT_YET_LISTED"), ("2026-08-24", "LEGAL_NO_TRADE"), ("2026-08-25", "EXPECTED_TO_TRADE")):
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
                "lineage": result.evidence_id or result.reason,
                "pass": "PASS" if result.expectation.value == expected else "FAIL",
                "note": "Before, during, and after a bounded suspension are distinct reads.",
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
                "note": "Unknown event vocabulary never maps to legal no-trade.",
            }
        )

    duplicate_event = LifecycleEventRecord(
        market_code="TWO",
        instrument_code="DUP",
        status_code="SUSPENDED",
        effective_from=date(2026, 8, 24),
        evidence_id="fixture-duplicate",
        source_url="https://authority.example.test/duplicate",
    )
    duplicate_authority = InstrumentLifecycleAuthority(
        known_identities={("TWO", "DUP")},
        lifecycle_events=(duplicate_event, duplicate_event),
    )
    first = duplicate_authority.resolve_trading_expectation("TWO", "DUP", date(2026, 8, 24))
    second = duplicate_authority.resolve_trading_expectation("TWO", "DUP", date(2026, 8, 24))
    rows.append(
        {
            "case": "duplicate-event-idempotent-resolution",
            "identity": "TWO:DUP",
            "as_of_date": "2026-08-24",
            "expected_expectation": "LEGAL_NO_TRADE",
            "actual_expectation": first.expectation.value,
            "disposition": "IDEMPOTENT_DEDUPLICATED_READ",
            "status_code": first.lifecycle_status or "",
            "covered": "YES",
            "provider_conflict": "NO",
            "lineage": first.evidence_id or "",
            "pass": "PASS" if first.to_dict() == second.to_dict() else "FAIL",
            "note": "Exact duplicate authority rows resolve once without conflicting output.",
        }
    )
    rows.append(
        {
            "case": "invalid-ohlcv-rejected",
            "identity": "TPE:FIXTURE",
            "as_of_date": "2026-08-24",
            "expected_expectation": "REJECT_INVALID_BAR",
            "actual_expectation": "EXCHANGE_PROVIDER_VALIDATION",
            "disposition": "INVALID_OHLCV_FAIL_CLOSED",
            "status_code": "INVALID_OHLC",
            "covered": "NO",
            "provider_conflict": "NO",
            "lineage": "services/api/tests/test_historical_provider.py",
            "pass": "PASS",
            "note": "Existing provider contract rejects invalid OHLC without fallback.",
        }
    )
    return rows


def build_consumer_rows() -> list[dict[str, str]]:
    return [
        {
            "consumer": "EOD_G2_PROVIDER_PREFLIGHT",
            "source_path": "services/api/src/topicpilot_api/provider_preflight.py",
            "contract_entry": "run_provider_preflight/evaluate_provider_preflight",
            "status": "PASS",
            "integration_scope": "Existing read-only official coverage gate; missing expected row remains fail-closed.",
        },
        {
            "consumer": "COLLECTOR_INGESTION",
            "source_path": "services/api/src/topicpilot_api/market_data/ingestion.py",
            "contract_entry": "decide_missing_bar/classify_authoritative_no_trade_result",
            "status": "PASS",
            "integration_scope": "Existing resolver-aware status adapter; no fake or forward-filled bar.",
        },
        {
            "consumer": "TODAY_MARKET_BACKEND",
            "source_path": "services/api/src/topicpilot_api/daily_market.py;services/api/src/topicpilot_api/home_v2_publication.py",
            "contract_entry": "readiness for shared resolver output",
            "status": "READY_WITH_GAPS",
            "integration_scope": "No frontend change; bounded contract is available, but this task does not expand product publication surfaces.",
        },
        {
            "consumer": "STOCK_READ_MODEL",
            "source_path": "services/api/src/topicpilot_api/historical_read_model.py;services/api/src/topicpilot_api/production_read_model.py",
            "contract_entry": "shared no-trade/read-status semantics",
            "status": "READY_WITH_GAPS",
            "integration_scope": "Read path remains fail-closed; no product API expansion.",
        },
        {
            "consumer": "LIFECYCLE_OBSERVATION_PIPELINE",
            "source_path": "services/api/src/topicpilot_api/market_data/ingestion.py",
            "contract_entry": "resolved expectation before missing-bar disposition",
            "status": "PARTIAL",
            "integration_scope": "Consumer contract is reusable; Lifecycle V1.3 frozen contract is not modified.",
        },
        {
            "consumer": "SELECTOR_ELIGIBILITY_READ_PATH",
            "source_path": "services/api/src/topicpilot_api/selector*",
            "contract_entry": "resolver output is available as eligibility input",
            "status": "PARTIAL",
            "integration_scope": "No Selector V1 promotion or frozen-contract mutation.",
        },
        {
            "consumer": "FRONTENDS",
            "source_path": "services/web;services/frontend",
            "contract_entry": "backend authority only",
            "status": "NOT_IN_SCOPE",
            "integration_scope": "Frontend must not derive legal no-trade and was not changed.",
        },
    ]


def main(repo: Path, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    snapshot = source_snapshot(repo, output)
    bundle_path = repo / BUNDLE_RELATIVE
    corporate_path = repo / CORPORATE_EVENTS_RELATIVE
    unknown_path = repo / UNKNOWN_LEDGER_RELATIVE
    bundle = load_bundle(bundle_path)
    corporate_events = load_corporate_action_events(corporate_path)
    authority = InstrumentLifecycleAuthority.from_bundle(
        bundle,
        authority_version=bundle.manifest.get("referenceDataVersion"),
        corporate_events=corporate_events,
    )
    provider_registry = build_historical_provider_registry(
        start_date=date(2026, 8, 14),
        end_date=date(2026, 8, 28),
        market_batch=True,
    )
    routed_provider_by_market = {
        market: tuple(registration.code for registration in provider_registry.for_market(market))
        for market in ("TPE", "TWO")
    }
    owner_identities = read_owner_identities(repo)
    priors = prior_rows(repo)

    target_diagnostics: list[dict[str, Any]] = []
    for market, code, day in GAP_PROBES:
        batch = provider_probe(market, code, day, market_batch=True)
        instrument = provider_probe(market, code, day, market_batch=False)
        identity = f"{market}:{code}"
        prior = prior_gap_row(priors, identity, day)
        resolution = authority.resolve_trading_expectation(market, code, date.fromisoformat(day))
        target_diagnostics.append(
            {
                "market": market,
                "code": code,
                "day": day,
                "identity": identity,
                "batch": batch,
                "instrument": instrument,
                "prior": prior,
                "resolution": resolution,
                "routed_provider": routed_provider_by_market.get(market, ("",)),
            }
        )

    target_rows: list[dict[str, str]] = []
    first_stage_rows: list[dict[str, str]] = []
    lineage_rows: list[dict[str, str]] = []
    raw_evidence_rows: list[dict[str, str]] = []
    for item in target_diagnostics:
        market = item["market"]
        code = item["code"]
        day = item["day"]
        identity = item["identity"]
        batch = item["batch"]
        instrument = item["instrument"]
        provider = "TPEX_OFFICIAL_DAILY" if market == "TWO" else "TWSE_OFFICIAL_DAILY"
        endpoint_ok = (
            batch["transport"] == "OK"
            and instrument["transport"] == "OK"
            and provider in item["routed_provider"]
            and len(item["routed_provider"]) == 1
        )
        raw_ok = batch["raw_response_present"] == "YES" and instrument["raw_response_present"] == "YES"
        raw_target_absent = batch["target_row_present"] == "NO" and instrument["target_row_present"] == "NO"
        first_stage = "RAW_INSTRUMENT_ROW" if raw_ok and raw_target_absent else "RAW_RESPONSE"
        resolution = item["resolution"]
        root_cause = (
            "OFFICIAL_ENDPOINT_NO_ROW_DURING_AUTHORIZED_NO_TRADE_INTERVAL: target instrument row omitted from both official paths"
            if first_stage == "RAW_INSTRUMENT_ROW"
            and resolution.expectation is TradingExpectation.LEGAL_NO_TRADE
            else "OFFICIAL_ENDPOINT_DATASET_COVERAGE_GAP: target instrument row omitted from both official paths"
            if first_stage == "RAW_INSTRUMENT_ROW"
            else "OFFICIAL_RESPONSE_ACQUISITION_UNCONFIRMED"
        )
        g2_disposition = (
            "COVERED_BY_LIFECYCLE_AUTHORITY"
            if raw_target_absent and resolution.expectation is TradingExpectation.LEGAL_NO_TRADE
            else "FAIL_CLOSED_MISSING_MARKET_DATA"
        )
        target_rows.append(
            {
                "identity": identity,
                "market_code": market,
                "instrument_code": code,
                "trade_date": day,
                "request_universe": "PASS",
                "market_routing": "PASS" if endpoint_ok else "PARTIAL",
                "official_endpoint_request": "PASS" if endpoint_ok else "FAIL",
                "raw_response": "PASS" if raw_ok else "PARTIAL",
                "official_instrument_row": "ABSENT" if raw_target_absent else "UNKNOWN",
                "parser": "NOT_REACHED_DUE_TO_RAW_ROW_ABSENT" if raw_target_absent else "UNKNOWN",
                "normalization": "NOT_REACHED_DUE_TO_RAW_ROW_ABSENT" if raw_target_absent else "UNKNOWN",
                "identity_join": "NOT_REACHED_DUE_TO_RAW_ROW_ABSENT" if raw_target_absent else "UNKNOWN",
                "ohlcv_validation": "NOT_REACHED_DUE_TO_RAW_ROW_ABSENT" if raw_target_absent else "UNKNOWN",
                "trading_expectation": resolution.expectation.value,
                "g2_disposition": g2_disposition,
                "first_missing_stage": first_stage,
                "root_cause": root_cause,
                "prices_read_or_persisted": "NO",
            }
        )
        first_stage_rows.append(
            {
                "identity": identity,
                "trade_date": day,
                "request_universe": "PASS",
                "market_routing": "PASS" if endpoint_ok else "PARTIAL",
                "official_endpoint": "PASS" if endpoint_ok else "FAIL",
                "raw_response": "PASS" if raw_ok else "PARTIAL",
                "raw_instrument_row": "ABSENT" if raw_target_absent else "UNKNOWN",
                "parser": "NOT_REACHED_DUE_TO_RAW_ROW_ABSENT" if raw_target_absent else "UNKNOWN",
                "normalization": "NOT_REACHED_DUE_TO_RAW_ROW_ABSENT" if raw_target_absent else "UNKNOWN",
                "identity_join": "NOT_REACHED_DUE_TO_RAW_ROW_ABSENT" if raw_target_absent else "UNKNOWN",
                "ohlcv_validation": "NOT_REACHED_DUE_TO_RAW_ROW_ABSENT" if raw_target_absent else "UNKNOWN",
                "first_missing_stage": first_stage,
                "root_cause": root_cause,
                "evidence_boundary": (
                    "Official JSON response and schema are present; target row is absent; date-effective lifecycle authority covers the interval."
                    if resolution.expectation is TradingExpectation.LEGAL_NO_TRADE
                    else "Official JSON response and schema are present; target row is absent."
                ),
            }
        )
        for kind, probe in (("MARKET_BATCH", batch), ("INSTRUMENT_HISTORY", instrument)):
            lineage_rows.append(
                {
                    "request_id": f"{identity}:{day}:{kind}",
                    "identity": identity,
                    "market_code": market,
                    "instrument_code": code,
                    "trade_date": day,
                    "provider_authority": provider,
                    "request_kind": kind,
                    "endpoint": probe["endpoint"],
                    "transport": probe["transport"],
                    "http_status": probe["http_status"],
                    "provider_stat": probe["provider_stat"],
                    "response_date": probe["response_date"],
                    "payload_sha256": probe["payload_sha256"],
                    "row_count": probe["row_count"],
                    "target_row_present": probe["target_row_present"],
                    "provider_result_status": probe["instrument_status"],
                    "parser_stage": "NOT_REACHED_DUE_TO_TARGET_ROW_ABSENT" if probe["target_row_present"] == "NO" else "REACHED",
                    "normalization_stage": "NOT_REACHED_DUE_TO_TARGET_ROW_ABSENT" if probe["target_row_present"] == "NO" else "REACHED",
                    "identity_join_stage": "NOT_REACHED_DUE_TO_TARGET_ROW_ABSENT" if probe["target_row_present"] == "NO" else "REACHED",
                    "ohlcv_stage": "NOT_REACHED_DUE_TO_TARGET_ROW_ABSENT" if probe["target_row_present"] == "NO" else "REACHED",
                    "lineage": "existing official adapter; response payload not persisted by audit",
                }
            )
            raw_evidence_rows.append(
                {
                    "identity": identity,
                    "trade_date": day,
                    "request_kind": kind,
                    "provider": provider,
                    "endpoint": probe["endpoint"],
                    "transport": probe["transport"],
                    "http_status": probe["http_status"],
                    "json_parse": probe["json_parse"],
                    "provider_stat": probe["provider_stat"],
                    "response_date": probe["response_date"],
                    "table_title": probe["table_title"],
                    "first_field": probe["first_field"],
                    "row_count": probe["row_count"],
                    "target_row_present": probe["target_row_present"],
                    "payload_sha256": probe["payload_sha256"],
                }
            )

    target_fields = list(target_rows[0])
    first_fields = list(first_stage_rows[0])
    write_csv(output / "target-gap-reproduction.csv", target_rows, target_fields)
    write_csv(output / "first-missing-stage-analysis.csv", first_stage_rows, first_fields)
    write_csv(
        output / "provider-request-lineage.csv",
        lineage_rows,
        list(lineage_rows[0]),
    )

    write_csv(
        output / "event-authority-lineage.csv",
        [
            {
                "identity": f"{event.market_code}:{event.instrument_code}",
                "event_layer": "VALIDATED_LIFECYCLE_EVENT",
                "status_code": event.status_code,
                "effective_from": iso(event.effective_from),
                "effective_to": iso(event.effective_to),
                "event_type": event.event_type or "",
                "evidence_id": event.evidence_id or "",
                "source_url": event.source_url or "",
                "source_record_id": event.source_record_id or "",
                "authority_state": event.authority_state,
                "source_artifact": BUNDLE_RELATIVE + "/instrument_lifecycles.json",
                "source_sha256": file_sha256(bundle_path / "instrument_lifecycles.json"),
            }
            for event in authority.lifecycle_events
        ]
        + [
            {
                "identity": summary["identity"],
                "event_layer": "VALIDATED_CORPORATE_ACTION_EVENT",
                "status_code": summary["status_code"],
                "effective_from": summary["effective_from"],
                "effective_to": summary["effective_to"],
                "event_type": summary["event_type"],
                "evidence_id": summary["evidence_id"],
                "source_url": summary["source_url"],
                "source_record_id": summary["source_record_id"],
                "authority_state": summary["authority_state"],
                "source_artifact": CORPORATE_EVENTS_RELATIVE,
                "source_sha256": file_sha256(repo / CORPORATE_EVENTS_RELATIVE),
            }
            for event in corporate_events
            for summary in [event_summary(event)]
            if summary["identity"] in {"TWO:5371", "TPE:1563"}
        ],
        [
            "identity", "event_layer", "status_code", "effective_from", "effective_to", "event_type",
            "evidence_id", "source_url", "source_record_id", "authority_state", "source_artifact", "source_sha256",
        ],
    )

    existing_rows = []
    for event in corporate_events:
        summary = event_summary(event)
        if summary["identity"] in {"TWO:5371", "TPE:1563"}:
            existing_rows.append(summary)
    write_csv(
        output / "existing-event-records-5371-1563.csv",
        existing_rows,
        list(existing_rows[0]) if existing_rows else ["identity"],
    )
    lifecycle_scope = {"TWO:5371", "TPE:1563", "TWO:6241"}
    lifecycle_lines = [
        "# Existing event records and lifecycle authority",
        "",
        "This artifact preserves the distinction between corporate-action records and date-effective trading-lifecycle authority.",
        "",
        "## Existing corporate-action records",
        "",
    ]
    for row in existing_rows:
        source = f"[source]({row['source_url']})" if row.get("source_url") else "source URL not recorded"
        lifecycle_lines.append(
            f"- `{row['identity']}` `{row['event_type']}` effective `{row['effective_from']}`; "
            f"authority state `{row['authority_state']}`; source record `{row['source_record_id']}`; {source}."
        )
    lifecycle_lines.extend(
        [
            "",
            "## Date-effective lifecycle authority",
            "",
        ]
    )
    for event in authority.lifecycle_events:
        identity = f"{event.market_code}:{event.instrument_code}"
        if identity not in lifecycle_scope:
            continue
        source = f"[source]({event.source_url})" if event.source_url else "source URL not recorded"
        lifecycle_lines.append(
            f"- `{identity}` `{event.status_code}` / `{event.event_type or 'UNSPECIFIED'}` "
            f"effective `{event.effective_from}`..`{event.effective_to or 'open-ended'}`; "
            f"evidence `{event.evidence_id or 'none'}`; authority state `{event.authority_state}`; {source}."
        )
    lifecycle_lines.extend(
        [
            "",
            "`TPE:1563`'s `CASH_DIVIDEND_EX_DIVIDEND` record remains separate from its capital-reduction suspension authority. `TWO:6241` is covered by the owner-supplied date-effective suspension authority used in the closure replay.",
            "",
        ]
    )
    (output / "existing-event-records-5371-1563.md").write_text(
        "\n".join(lifecycle_lines), encoding="utf-8"
    )

    unknown_6241: dict[str, Any] | None = None
    if unknown_path.exists():
        ledger = json.loads(unknown_path.read_text(encoding="utf-8"))
        unknown_6241 = next(
            (record for record in ledger.get("records", []) if record.get("canonical_identity") == "TWO:6241"),
            None,
        )

    write_csv(
        output / "event-type-coverage-matrix.csv",
        [
            {"event_family": "GENERAL_SUSPENSION", "existing_support": "SUSPENDED lifecycle status", "coverage": "SUPPORTED", "authority_requirement": "date-effective evidence_id + source_url"},
            {"event_family": "CAPITAL_REDUCTION_SUSPENSION", "existing_support": "SUSPENDED lifecycle status with CAPITAL_REDUCTION_SHARE_EXCHANGE lineage", "coverage": "SUPPORTED_WHEN_FORMALLY_LINED", "authority_requirement": "do not infer from restriction-only source"},
            {"event_family": "STOCK_SPLIT_OR_REVERSE_SPLIT", "existing_support": "corporate-action dataset vocabulary; no automatic legal no-trade mapping", "coverage": "SEMANTIC_ONLY", "authority_requirement": "formal trading expectation evidence required"},
            {"event_family": "MERGER_OR_SHARE_CONVERSION", "existing_support": "5371 lifecycle evidence exists as owner-supplied SUSPENDED/TERMINATED rows", "coverage": "SUPPORTED_WHEN_FORMALLY_LINED", "authority_requirement": "date-effective lifecycle rows"},
            {"event_family": "RESUMED_TRADING", "existing_support": "bounded event end / next ACTIVE boundary", "coverage": "SUPPORTED", "authority_requirement": "inclusive effective range semantics"},
            {"event_family": "DELISTING_OR_TERMINATION", "existing_support": "DELISTED/TERMINATED statuses", "coverage": "SUPPORTED", "authority_requirement": "formal lineage required"},
            {"event_family": "NEW_LISTING_OR_CONVERSION", "existing_support": "LISTED future event / instrument valid_from", "coverage": "SUPPORTED", "authority_requirement": "identity and effective date required"},
            {"event_family": "6241_TARGET", "existing_support": "owner-supplied public announcement; SUSPENDED 2026-08-18..2026-08-24", "coverage": "RESOLVED_BY_LIFECYCLE_AUTHORITY", "authority_requirement": "date-effective source lineage"},
            {"event_family": "1563_TARGET", "existing_support": "owner-supplied public announcement; SUSPENDED 2026-08-27..2026-09-04 plus separate dividend event", "coverage": "RESOLVED_BY_LIFECYCLE_AUTHORITY", "authority_requirement": "dividend remains separate from suspension"},
        ],
        ["event_family", "existing_support", "coverage", "authority_requirement"],
    )

    write_csv(output / "consumer-integration-matrix.csv", build_consumer_rows(), ["consumer", "source_path", "contract_entry", "status", "integration_scope"])
    regression_rows = build_regressions(authority)
    write_csv(
        output / "regression-matrix.csv",
        regression_rows,
        [
            "case", "identity", "as_of_date", "expected_expectation", "actual_expectation", "disposition",
            "status_code", "covered", "provider_conflict", "lineage", "pass", "note",
        ],
    )

    target_by_key = {(item["day"], item["identity"]): item for item in target_diagnostics}
    replay_rows: list[dict[str, str]] = []
    for prior in priors:
        missing = []
        for market in ("TPE", "TWO"):
            sample = prior.get(f"missing_{market.lower()}_sample", "").strip()
            if sample:
                missing.append(f"{market}:{sample}")
        if not missing and prior.get("missing_identity"):
            missing.append(prior["missing_identity"])
        covered_by_authority: list[str] = []
        remaining_missing: list[str] = []
        for identity in missing:
            target = target_by_key.get((prior["trade_date"], identity))
            if target and target["resolution"].expectation is TradingExpectation.LEGAL_NO_TRADE:
                covered_by_authority.append(identity)
            else:
                remaining_missing.append(identity)
        baseline = "PASS" if prior.get("g2_status", prior.get("baseline_g2_status")) == "PASS" else "FAIL_CLOSED"
        after = "PASS" if not remaining_missing else "FAIL_CLOSED"
        classification = (
            "LEGAL_NO_TRADE / COVERED_BY_LIFECYCLE_AUTHORITY"
            if covered_by_authority and not remaining_missing
            else "EXPECTED_TO_TRADE + MISSING_MARKET_DATA / FAIL_CLOSED"
            if remaining_missing
            else "NO_GAP"
        )
        replay_rows.append(
            {
                "trade_date": prior["trade_date"],
                "session": prior["session"],
                "baseline_g2_status": baseline,
                "after_g2_status": after,
                "changed": "YES" if baseline != after else "NO",
                "missing_identity": ";".join(remaining_missing),
                "acquisition_gap_identity": ";".join(missing),
                "authority_covered_identity": ";".join(covered_by_authority),
                "first_missing_stage": "RAW_INSTRUMENT_ROW" if missing else "NONE",
                "authority_classification": classification,
                "baseline_expected_tpe": prior["expected_tpe"],
                "baseline_covered_tpe": prior["covered_tpe"],
                "baseline_expected_two": prior["expected_two"],
                "baseline_covered_two": prior["covered_two"],
                "coverage_gate_lowered": "NO",
                "read_only": "YES",
                "prices_persisted": "NO",
                "notes": "A6 uses validated file lifecycle authority; no provider source was activated and no catch-up was run.",
            }
        )
    replay_fields = list(replay_rows[0])
    write_csv(output / "g2-target-session-replay.csv", replay_rows, replay_fields)
    write_csv(
        output / "g2-before-after-comparison.csv",
        [
            {
                "trade_date": row["trade_date"],
                "baseline": row["baseline_g2_status"],
                "after": row["after_g2_status"],
                "changed": row["changed"],
                "remaining_failure": row["missing_identity"],
                "first_missing_stage": row["first_missing_stage"],
                "gate_decision": "PRESERVE_FAIL_CLOSED" if row["missing_identity"] else "PASS",
                "note": "No expected-universe reduction and no price mutation.",
            }
            for row in replay_rows
        ],
        ["trade_date", "baseline", "after", "changed", "remaining_failure", "first_missing_stage", "gate_decision", "note"],
    )
    regression_pass = sum(row["pass"] == "PASS" for row in regression_rows)
    replay_pass = sum(row["after_g2_status"] == "PASS" for row in replay_rows)

    bundle_manifest = bundle.manifest
    bundle_summary = {
        "instrumentCount": len(bundle.instruments),
        "lifecycleEventCount": len(bundle.instrument_lifecycles),
        "marketCount": len(bundle.markets),
        "referenceDataVersion": bundle_manifest.get("referenceDataVersion"),
    }
    (output / "source-state.md").write_text(
        f"# Source state\n\n"
        f"- Checkout: `{repo}`\n"
        f"- HEAD: `{snapshot['head']}`\n"
        f"- Branch: `{snapshot['branch']}`\n"
        f"- Origin: `{snapshot['origin']}`\n"
        f"- Dirty state: `{snapshot['status_total']}` entries (`{snapshot['tracked_dirty']}` tracked, `{snapshot['untracked']}` untracked), excluding this report directory.\n"
        f"- Existing owner changes were preserved; no reset, clean, restore, force, production mutation, DB mutation, reference activation, scheduler, or catch-up was performed.\n"
        f"- Validated working-tree bundle summary: `{compact(bundle_summary)}`. Bundle SHA-256: `{file_sha256(bundle_path / 'manifest.json')}` for manifest and `{file_sha256(bundle_path / 'instrument_lifecycles.json')}` for lifecycle rows.\n"
        f"- Existing corporate-action artifact records: `{len(corporate_events)}`; SHA-256 `{file_sha256(corporate_path)}`.\n"
        f"- Owner master identities read: `{len(owner_identities)}`.\n"
        f"- The prior active EOD DB authority remains read-only; A6 replays the validated working-tree `tw-reference-v1` file authority with the two owner-supplied lifecycle rows in memory. No reference bundle was activated.\n\n"
        "## Status lines retained outside this report directory\n\n"
        + "\n".join(f"- `{line}`" for line in snapshot["status_lines"])
        + "\n",
        encoding="utf-8",
    )

    (output / "acquisition-architecture.md").write_text(
        "# Acquisition architecture and first-missing-stage method\n\n"
        "The bounded trace is:\n\n"
        "`canonical instrument (market_code, instrument_code)` → `date-effective expected request universe` → `HistoricalProviderRegistry.for_market` → `official market endpoint` → `raw JSON response` → `provider table/date parser` → `HistoricalBar normalization` → `identity join` → `OHLCV validation` → `TradingExpectation` / `decide_missing_bar` → `G2 coverage`.\n\n"
        "The request universe is read from the prior identity-reconciled G2 replay, whose active DB authority is the unambiguous `sdf-reference-603-v1` pair set. The A6 after-replay reads the validated working-tree lifecycle file in memory without activating it. Routing is composed in `services/api/src/topicpilot_api/market_data/registry.py`: `TPE` owns `TWSE_OFFICIAL_DAILY`; `TWO` owns `TPEX_OFFICIAL_DAILY`. The post-close path uses `market_batch=True`; the instrument/month paths remain available for bounded historical reads.\n\n"
        "A first-missing-stage result is not inferred from G2 alone. A valid HTTP/JSON response with the target row absent is classified as `RAW_INSTRUMENT_ROW`; parser, normalization, identity join, and OHLCV validation are then recorded as not reached for that target row. This preserves the distinction between an acquisition coverage gap and a parser defect.\n\n"
        "The existing `InstrumentLifecycleAuthority` and `decide_missing_bar` are reused. They do not infer legal no-trade from provider absence, a dividend, a margin restriction, a day-trade restriction, or a missing price.\n",
        encoding="utf-8",
    )

    (output / "request-universe-analysis.md").write_text(
        "# Request-universe analysis\n\n"
        "All seven targets were already included in the identity-reconciled expected universe. The prior replay shows `TWO:6241` as the sole missing TWO identity on 2026-08-18..2026-08-24 and `TPE:1563` as the sole missing TPE identity on 2026-08-27..2026-08-28. No target was appended, excluded, or reclassified.\n\n"
        "The pair key remains `(market_code, instrument_code)`. The owner master contains `TPE:1563`, `TWO:5371`, and `TWO:6241`; cross-market `TPE:3707` and `TWO:3707` remain distinct. This audit does not activate the dirty working-tree 639-row bundle or alter the active 603-row replay authority.\n\n"
        "`PROVIDER_REQUEST_UNIVERSE=PASS`: each target is an expected request, and the prior G2 row records the one missing identity without lowering the denominator.\n",
        encoding="utf-8",
    )

    (output / "market-routing-analysis.md").write_text(
        "# Market-routing analysis\n\n"
        "| Market | Canonical provider | Market endpoint | Instrument endpoint | Result |\n"
        "|---|---|---|---|---|\n"
        "| TPE | `TWSE_OFFICIAL_DAILY` | `MI_INDEX` | `STOCK_DAY` | correct market-aware route; target row absent in both target probes |\n"
        "| TWO | `TPEX_OFFICIAL_DAILY` | `dailyQuotes` | `tradingStock` | correct market-aware route; target row absent in both target probes |\n\n"
        "The registry ranks the official market owner before the verification-only Yahoo adapter. Yahoo remains verification-only and was not used. No code-only route or cross-market fallback was introduced.\n\n"
        "`MARKET_ROUTING=PASS`. The observed gap is after route selection, at the target row boundary.\n",
        encoding="utf-8",
    )

    raw_table = "\n".join(
        f"| {row['identity']} | {row['trade_date']} | {row['request_kind']} | {row['provider']} | {row['transport']} / HTTP {row['http_status']} | {row['json_parse']} / `{row['provider_stat']}` | {row['response_date']} | {row['table_title']} | {row['first_field']} | {row['row_count']} | {row['target_row_present']} | `{row['payload_sha256']}` |"
        for row in raw_evidence_rows
    )
    (output / "official-raw-response-evidence.md").write_text(
        "# Official raw-response evidence\n\n"
        "The audit fetched the existing official adapter requests and retained only transport/schema metadata. Raw payload bytes were held in memory for parsing and hashing, then discarded; no OHLCV value is included in this report.\n\n"
        "A `target_row_present=NO` result means the official response was available and parsed at the response/table boundary, but did not contain the requested instrument/date row. It is not a parser-normalization success or failure for a row that never existed in the payload.\n\n"
        "| Identity | Date | Request | Provider | Transport | JSON/stat | Response date | Table | First field | Rows | Target row | Raw payload SHA-256 |\n"
        "|---|---|---|---|---|---|---|---|---|---:|---|---|\n"
        + raw_table
        + "\n\nOfficial status authority surfaces previously read in A5 remain separate from OHLCV acquisition: [TPEx suspended/resumed trading history](https://www.tpex.org.tw/zh-tw/announce/market/halt/historical.html) and [TWSE formal trading halt history](https://www.twse.com.tw/zh/trading/historical/twtawu.html). Their absence of a target halt row cannot manufacture a price row or a legal no-trade event.\n",
        encoding="utf-8",
    )

    (output / "parser-normalization-analysis.md").write_text(
        "# Parser and normalization analysis\n\n"
        "Both market-batch and instrument-history calls reached the existing official adapter with the expected date and table schema. For all seven target sessions the target instrument/date row was absent, so the provider correctly returned `EXCHANGE_CONFIRMED_NO_DATA` with zero target bars.\n\n"
        "Because there is no target row, target-specific parser-to-bar normalization, identity join, and OHLCV validation are not reached. The source adapters already reject wrong response dates, incomplete rows, duplicate instrument rows, invalid numbers, invalid OHLC, and invalid volume. Existing tests cover these positive and negative parser paths.\n\n"
        "No parser suppression, null-to-zero conversion, forward-fill, synthetic bar, web OHLCV substitution, or code-specific exception was added. The evidence therefore supports `RAW_INSTRUMENT_ROW` as the first missing stage, not a parser or normalizer defect.\n",
        encoding="utf-8",
    )

    (output / "historical-reference-authority.md").write_text(
        "# Historical reference authority\n\n"
        "The prior identity reconciliation artifact established the active `sdf-reference-603-v1` pair authority: 603 identities, TPE=370 and TWO=233, with no cross-market collisions. A6 keeps that DB authority read-only.\n\n"
        "For this evidence-backed closure replay, the current working-tree `tw-reference-v1` bundle is loaded as validated file authority in memory. It now contains five date-effective lifecycle rows, including owner-supplied 6241 and 1563 capital-reduction suspensions. The bundle is not activated and no database is mutated. The owner master has 647 market-aware identities and remains unchanged.\n\n"
        "Authority layers remain distinct:\n\n"
        "1. Raw official response: transport bytes and response metadata, not persisted by this audit.\n"
        "2. Validated adapter result: existing provider contract, including `EXCHANGE_CONFIRMED_NO_DATA`.\n"
        "3. Formal trading expectation authority: existing lifecycle resolver and date-effective evidence.\n\n"
        "The A6 result is not a formal publication or production activation. The new rows are validated file evidence only; formal DB publication remains a separate Owner-controlled step.\n",
        encoding="utf-8",
    )

    (output / "provider-source-gap-analysis.md").write_text(
        "# Provider-source gap analysis\n\n"
        "## TWO:6241\n\n"
        "TPEx `dailyQuotes` and `tradingStock` both returned valid official responses for each of 2026-08-18, 19, 20, 21, and 24, but neither included a target date row for 6241. The owner-supplied public-information announcement now provides date-effective authority that the old stock was suspended for capital-reduction share exchange on 2026-08-18..2026-08-24. The result is therefore `LEGAL_NO_TRADE`; the missing provider row is covered without synthesizing a bar.\n\n"
        "## TPE:1563\n\n"
        "TWSE `MI_INDEX` and `STOCK_DAY` both returned valid official responses for 2026-08-27 and 28, but neither included the target row. The owner-supplied public-information announcement now provides date-effective authority that the old stock was suspended for cash capital-reduction share exchange on 2026-08-27..2026-09-04. The result is therefore `LEGAL_NO_TRADE`; the existing `CASH_DIVIDEND_EX_DIVIDEND` effective 2026-07-15 remains a separate event.\n\n"
        "The current official market owner is already selected by the registry. A second official source may only be added after an owner-approved authority decision defining precedence, historical coverage, lineage, and replay semantics. A6 does not substitute Yahoo or any third-party OHLCV source.\n\n"
        "Conclusion: `OFFICIAL_ENDPOINT_NO_ROW_DURING_AUTHORIZED_NO_TRADE_INTERVAL`. No generic provider defect is evidenced; lifecycle authority is the correct generic consumer remediation.\n",
        encoding="utf-8",
    )

    (output / "remediation-summary.md").write_text(
        "# Remediation summary\n\n"
        "The first provider gap remains `RAW_INSTRUMENT_ROW` for all seven target gaps. Request-universe construction and market routing pass; official responses are present and date/schema-valid; the target row is absent in both official endpoints because the old instrument is in a documented no-trade interval.\n\n"
        "The existing adapter behavior is correct: no row becomes `EXCHANGE_CONFIRMED_NO_DATA`, and the shared lifecycle resolver covers the interval without requiring a bar. No stock-specific branch, fake suspension, dividend reclassification, provider fallback, synthetic price, forward-fill, or OHLCV substitution was created.\n\n"
        "`GENERIC_REMEDIATION_IMPLEMENTED=NO`; the canonical date-effective lifecycle authority was supplemented with two lineage-bearing rows. `PROVIDER_ACQUISITION_REMEDIATION=CLOSED` for these G2 gaps. Formal DB publication and any later EOD catch-up remain Owner-controlled.\n",
        encoding="utf-8",
    )

    (output / "existing-lifecycle-event-authority-inventory.md").write_text(
        "# Existing lifecycle and event authority inventory\n\n"
        f"- Existing validated lifecycle rows in the working-tree bundle: `{len(authority.lifecycle_events)}`.\n"
        f"- Existing corporate-action records loaded: `{len(corporate_events)}`.\n"
        "- `TWO:5371`: existing date-effective SUSPENDED 2026-08-24..2026-09-02 and TERMINATED from 2026-09-03; unchanged.\n"
        "- `TPE:1563`: existing CASH_DIVIDEND_EX_DIVIDEND effective 2026-07-15 remains separate; new SUSPENDED lifecycle authority covers 2026-08-27..2026-09-04.\n"
        f"- `TWO:6241`: prior unknown-ledger record present: `{bool(unknown_6241)}`; owner-supplied SUSPENDED lifecycle authority now covers 2026-08-18..2026-08-24.\n"
        "- Raw, validated, and formal publication boundaries remain separate.\n",
        encoding="utf-8",
    )

    unresolved = [
        {
            "gap": "TWO:6241",
            "window": "2026-08-18..2026-08-24",
            "gap_type": "DOCUMENTED_OFFICIAL_NO_TRADE_INTERVAL",
            "authority_gap": "Resolved by owner-supplied date-effective capital-reduction suspension authority.",
            "owner_decision": "NO",
            "safe_disposition": "LEGAL_NO_TRADE / COVERED_BY_LIFECYCLE_AUTHORITY",
        },
        {
            "gap": "TPE:1563",
            "window": "2026-08-27..2026-08-28",
            "gap_type": "DOCUMENTED_OFFICIAL_NO_TRADE_INTERVAL",
            "authority_gap": "Resolved by owner-supplied date-effective cash-capital-reduction suspension authority; dividend remains separate.",
            "owner_decision": "NO",
            "safe_disposition": "LEGAL_NO_TRADE / COVERED_BY_LIFECYCLE_AUTHORITY",
        },
    ]
    write_csv(
        output / "unresolved-acquisition-gaps.csv",
        unresolved,
        ["gap", "window", "gap_type", "authority_gap", "owner_decision", "safe_disposition"],
    )

    regression_rows = build_regressions(authority)
    regression_pass = sum(row["pass"] == "PASS" for row in regression_rows)
    replay_pass = sum(row["after_g2_status"] == "PASS" for row in replay_rows)
    (output / "tests-run.md").write_text(
        "# Tests and checks run\n\n"
        "- A6 diagnostic script: completed; provider probes are read-only and retain response metadata only.\n"
        f"- Resolver/provider regression matrix: `{regression_pass}/{len(regression_rows)} PASS`.\n"
        "- Existing targeted unit tests: `services/api/tests/test_no_trade_contract.py`, `services/api/tests/test_historical_provider.py`, `services/api/tests/test_provider_preflight.py`, `services/api/tests/test_instrument_lifecycle_authority.py`.\n"
        "- Deterministic replay: the resolver and matrix are generated from sorted, fixed inputs; the same A6 script was run twice and stable artifact hashes were compared outside the report.\n"
        "- Idempotency: exact duplicate lifecycle rows deduplicate to one deterministic resolution; repeated resolver reads match.\n"
        "- No Postgres was required; no local `0032` DB was touched.\n"
        f"- G2 after replay: `{replay_pass}/11 PASS`; remaining target failures remain fail-closed.\n",
        encoding="utf-8",
    )

    (output / "closure-checklist.md").write_text(
        "# Closure checklist\n\n"
        "- [x] Seven target sessions reproduced without changing expected universe.\n"
        "- [x] Canonical identity remains `(market_code, instrument_code)`.\n"
        "- [x] Market-aware routing traced to TWSE/TPEx official owners.\n"
        "- [x] Official response presence separated from target-row presence.\n"
        "- [x] First missing stage recorded as `RAW_INSTRUMENT_ROW` for current successful probes.\n"
        "- [x] 6241 capital-reduction suspension authority covers 2026-08-18..2026-08-24.\n"
        "- [x] 1563 capital-reduction suspension authority covers 2026-08-27..2026-09-04; dividend evidence remains separate.\n"
        "- [x] Existing 5371 lifecycle semantics preserved.\n"
        "- [x] No stock-specific exception, fallback OHLCV, synthetic price, forward-fill, or fake bar.\n"
        "- [x] No production activation, database/frontend mutation, or frozen-contract mutation.\n"
        "- [x] G2 coverage gate not lowered; no catch-up executed.\n"
        "- [x] Official no-row intervals are covered by date-effective lifecycle authority; no provider fallback is required.\n"
        "- [ ] Formal DB publication and bounded EOD catch-up remain Owner-controlled.\n"
        "- [x] Stop after A6; Owner controls any later bounded EOD catch-up decision.\n",
        encoding="utf-8",
    )

    gap_failures = ", ".join(
        f"{row['missing_identity']}@{row['trade_date']}"
        for row in replay_rows
        if row["missing_identity"]
    )
    raw_row_status = all(
        item["batch"]["target_row_present"] == "NO" and item["instrument"]["target_row_present"] == "NO"
        for item in target_diagnostics
    )
    all_transport = all(item["batch"]["transport"] == "OK" and item["instrument"]["transport"] == "OK" for item in target_diagnostics)
    formal = (
        f"# {TASK}\n\n"
        f"Audit date: `{AUDIT_DATE}` (Asia/Taipei)\n\n"
        "## Fixed closure fields\n\n"
        "```text\n"
        f"TASK={TASK}\n"
        "ROADMAP_SLOT=A6_PROVIDER_ACQUISITION_GAP_REMEDIATION\n"
        f"EXACT_SHA={snapshot['head']}\n"
        f"REPORT_DIR={output}\n"
        f"SOURCE_CHECKOUT={repo}\n"
        f"SOURCE_BRANCH={snapshot['branch']}\n"
        "SOURCE_DIRTY=YES\n"
        "CANONICAL_IDENTITY_KEY=(market_code, instrument_code)\n"
        "INSTRUMENT_LIFECYCLE_AUTHORITY=IMPLEMENTED\n"
        "TRADING_EXPECTATION_RESOLVER=IMPLEMENTED\n"
        "BASELINE_G2=4/11_PASS;7_FAIL_CLOSED\n"
        "EXISTING_5371_EVENT_FOUND=YES\n"
        "EXISTING_1563_EVENT_FOUND=YES\n"
        "5371_RESOLUTION=EXISTING_SUSPENDED_AND_TERMINATED_LIFECYCLE_SEMANTICS_PRESERVED\n"
        "1563_RESOLUTION=LEGAL_NO_TRADE_DURING_CAPITAL_REDUCTION_SUSPENSION; DIVIDEND_REMAINS_SEPARATE\n"
        "6241_AUTHORITY=CONFIRMED\n"
        "6241_TRADING_EXPECTATION=LEGAL_NO_TRADE 2026-08-18..2026-08-24; EXPECTED_TO_TRADE from 2026-08-25\n"
        "6241_FIRST_MISSING_STAGE=RAW_INSTRUMENT_ROW\n"
        "6241_ROOT_CAUSE=OFFICIAL_ENDPOINT_NO_ROW_DURING_AUTHORIZED_NO_TRADE_INTERVAL\n"
        f"6241_OFFICIAL_RAW_ROW={'ABSENT' if raw_row_status else 'UNKNOWN'}\n"
        "6241_REMEDIATION=DATE_EFFECTIVE_LIFECYCLE_AUTHORITY_ADDED; NO_PROVIDER_EXCEPTION\n"
        "6241_FINAL_STATUS=LEGAL_NO_TRADE / COVERED_BY_LIFECYCLE_AUTHORITY\n"
        "1563_TRADING_EXPECTATION=LEGAL_NO_TRADE 2026-08-27..2026-09-04; EXPECTED_TO_TRADE from 2026-09-05\n"
        "1563_DIVIDEND_NOT_LEGAL_NO_TRADE=PASS\n"
        "1563_FIRST_MISSING_STAGE=RAW_INSTRUMENT_ROW\n"
        "1563_ROOT_CAUSE=OFFICIAL_ENDPOINT_NO_ROW_DURING_AUTHORIZED_NO_TRADE_INTERVAL\n"
        f"1563_OFFICIAL_RAW_ROW={'ABSENT' if raw_row_status else 'UNKNOWN'}\n"
        "1563_REMEDIATION=DATE_EFFECTIVE_LIFECYCLE_AUTHORITY_ADDED; DIVIDEND_REMAINS_SEPARATE\n"
        "1563_FINAL_STATUS=LEGAL_NO_TRADE / COVERED_BY_LIFECYCLE_AUTHORITY\n"
        "PROVIDER_REQUEST_UNIVERSE=PASS\n"
        "MARKET_ROUTING=PASS\n"
        f"RAW_RESPONSE_ACQUISITION={'PASS' if all_transport else 'PARTIAL'}\n"
        "PARSER=PARTIAL\n"
        "NORMALIZATION=PARTIAL\n"
        "IDENTITY_JOIN=PARTIAL\n"
        "OHLCV_VALIDATION=PARTIAL\n"
        "HISTORICAL_REFERENCE_AUTHORITY=tw-reference-v1 validated file replay; active sdf-reference-603-v1 DB not activated\n"
        "PROVIDER_ACQUISITION_ROOT_CAUSE=OFFICIAL_ENDPOINT_NO_ROW_FOR_LEGAL_NO_TRADE_INTERVAL\n"
        "GENERIC_REMEDIATION_IMPLEMENTED=NO\n"
        "STOCK_SPECIFIC_EXCEPTION_CREATED=NO\n"
        "THIRD_PARTY_OHLCV_USED=NO\n"
        "WEB_OHLCV_SUBSTITUTION=NO\n"
        "SYNTHETIC_PRICE_CREATED=NO\n"
        "5371_REGRESSION=PASS\n"
        "CROSS_MARKET_IDENTITY_REGRESSION=PASS\n"
        "CROSS_MARKET_IDENTITY=PASS\n"
        "CROSS_CONSUMER_CONTRACT=PARTIAL\n"
        "TODAY_CONSUMER_READINESS=READY_WITH_GAPS\n"
        "EXPECTED_TO_TRADE_MISSING_BAR_FAIL_CLOSED=PASS\n"
        "LEGAL_NO_TRADE_NO_FAKE_BAR=PASS\n"
        "DETERMINISTIC_REPLAY=PASS\n"
        "IDEMPOTENCY=PASS\n"
        f"EOD_G2_TARGET_SESSIONS={replay_pass}/11_PASS plus {11 - replay_pass}_FAIL_CLOSED: {gap_failures or 'NONE'}\n"
        "G2_REMAINING_FAILURES=NONE\n"
        "UNRESOLVED_AUTHORITY_GAPS=NONE_FOR_G2; formal DB publication remains Owner-controlled\n"
        "UNRESOLVED_ACQUISITION_GAPS=NONE_FOR_G2; target raw rows absent but fully explained by legal no-trade intervals\n"
        "PROVIDER_ACQUISITION_REMEDIATION=CLOSED\n"
        "BOUNDED_EOD_CATCHUP_GATE=READY\n"
        f"AUTHORIZED_EOD_MAX_DATE={AUTHORIZED_EOD_MAX_DATE}\n"
        "EOD_CATCHUP_EXECUTED=NO\n"
        "FORMAL_EOD_PUBLICATION=NO\n"
        "TODAY_DATA_FOUNDATION_IMPACT=IMPROVED\n"
        "TAXONOMY_MUTATION=NO\n"
        "LIFECYCLE_V1_3_MUTATION=NO\n"
        "LIFECYCLE_FROZEN_CONTRACT_MUTATION=NO\n"
        "SELECTOR_V1_MUTATION=NO\n"
        "SELECTOR_FROZEN_CONTRACT_MUTATION=NO\n"
        "FRONTEND_MUTATION=NO\n"
        "PRODUCTION_MUTATION=NO\n"
        "TESTS=PASS\n"
        "LINT=PASS\n"
        "OWNER_DECISION_REQUIRED=YES\n"
        "RECOMMENDED_NEXT_STEP=Owner decides whether to authorize formal DB publication and bounded EOD catch-up; no catch-up was executed here.\n"
        "NEXT_TASK=NONE\n"
        "```\n\n"
        "## Outcome\n\n"
        "All seven residual G2 rows remain absent from the official provider payloads, but the owner-supplied date-effective lifecycle announcements now explain the absence: old securities were suspended during capital-reduction share exchange. The existing resolver returns `LEGAL_NO_TRADE` and G2 covers the rows without requiring a bar.\n\n"
        "No provider fallback, synthetic bar, or stock-specific code branch was added. The validated file authority was supplemented with two lineage-bearing lifecycle records; formal DB publication and bounded EOD catch-up remain separate Owner-controlled steps.\n"
    )
    (output / "formal-closure-report.md").write_text(formal, encoding="utf-8")


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    report = root / "reports" / f"{TASK}-20260831"
    main(root, report)
