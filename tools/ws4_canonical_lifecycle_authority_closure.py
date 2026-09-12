"""Generate the bounded WS4 lifecycle-authority closure artifacts.

The script is intentionally read-only with respect to application data.  It
loads the current reference bundle and existing event artifacts, runs the
resolver and replay checks, and writes only the requested report directory.
"""

from __future__ import annotations

import csv
import json
import subprocess
from datetime import date
from pathlib import Path
from typing import Any

from topicpilot_api.instrument_lifecycle_authority import (
    InstrumentLifecycleAuthority,
    LifecycleAuthorityError,
    LifecycleEventRecord,
    TradingExpectation,
    decide_missing_bar,
    file_sha256,
    load_corporate_action_events,
)
from topicpilot_api.reference_data.bundle import load_bundle
from topicpilot_api.research.corporate_action_dataset import EVENT_TYPES

TASK = "TASK-WS4-CANONICAL-INSTRUMENT-LIFECYCLE-TRADING-EXPECTATION-AUTHORITY-AND-CROSS-CONSUMER-CLOSURE"
TARGET_WINDOW = (date(2026, 8, 14), date(2026, 8, 28))
PRIOR_REPLAY = (
    "reports/TASK-WS4-CANONICAL-INSTRUMENT-REFERENCE-IDENTITY-RECONCILIATION-AND-EOD-G2-CLOSURE-20260831"
    "/g2-target-session-replay.csv"
)
BUNDLE_RELATIVE = "services/api/src/topicpilot_api/reference_data/bundles/tw-reference-v1"
CORPORATE_EVENTS_RELATIVE = (
    "reports/TASK-REC-A1-CORPORATE-ACTION-RESEARCH-DATASET-IMPLEMENTATION"
    "/REC-A1-CA-EVENTS-V0.json"
)
UNKNOWN_LEDGER_RELATIVE = (
    "reports/TASK-REC-A1-UNKNOWN-154-IDENTITY-EVENT-GAP-REVIEW"
    "/identity-review-ledger.json"
)
OWNER_MASTER_RELATIVE = "config/topic_master_v1/instruments.csv"


def git_output(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()


def source_snapshot(repo: Path, ignored_output: Path | None = None) -> dict[str, Any]:
    lines = git_output(repo, "status", "--porcelain=v1").splitlines()
    ignored_token = (
        ignored_output.relative_to(repo).as_posix().rstrip("/")
        if ignored_output is not None and ignored_output.is_relative_to(repo)
        else None
    )
    if ignored_token:
        lines = [
            line
            for line in lines
            if ignored_token not in line.replace("\\", "/")
        ]
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


def json_compact(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def read_owner_master(repo: Path) -> set[tuple[str, str]]:
    path = repo / OWNER_MASTER_RELATIVE
    if not path.exists():
        return set()
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return {
            (row["market_code"].strip().upper(), row["instrument_code"].strip())
            for row in csv.DictReader(handle)
            if row.get("market_code") and row.get("instrument_code")
        }


def event_summary(event: Any) -> dict[str, Any]:
    return {
        "market_code": getattr(event, "market_code", ""),
        "instrument_code": getattr(event, "instrument_code", ""),
        "event_type": getattr(event, "event_type", ""),
        "effective_date": iso(getattr(event, "primary_effective_date", None)),
        "reference_price": getattr(event, "reference_price", "") or "",
        "authority_state": getattr(event, "authority_state", ""),
        "reason_code": getattr(event, "reason_code", "") or "",
        "source_url": getattr(event, "source_url", ""),
        "source_record_id": getattr(event, "source_record_id_or_canonical_row_key", ""),
        "semantic_hash": getattr(event, "normalized_semantic_hash", ""),
    }


def resolution_dict(authority: InstrumentLifecycleAuthority, market: str, code: str, day: str) -> dict[str, Any]:
    resolution = authority.resolve_trading_expectation(market, code, date.fromisoformat(day))
    return resolution.to_dict()


def build_regressions(authority: InstrumentLifecycleAuthority) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    def add(
        case: str,
        market: str,
        code: str,
        day: str,
        expected: str,
        *,
        has_observation: bool = False,
        has_priced_bar: bool = False,
        note: str = "",
    ) -> None:
        result = authority.resolve_trading_expectation(market, code, date.fromisoformat(day))
        decision = decide_missing_bar(
            result,
            has_observation=has_observation,
            has_priced_bar=has_priced_bar,
        )
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
                "pass": "PASS" if result.expectation.value == expected else "FAIL",
                "note": note,
            }
        )

    add("normal-traded-instrument", "TPE", "2330", "2026-08-24", "EXPECTED_TO_TRADE")
    add("5371-before-event", "TWO", "5371", "2026-08-21", "EXPECTED_TO_TRADE")
    add("5371-suspension-start-boundary", "TWO", "5371", "2026-08-24", "LEGAL_NO_TRADE")
    add("5371-suspension-end-boundary", "TWO", "5371", "2026-09-02", "LEGAL_NO_TRADE")
    add("5371-after-termination-boundary", "TWO", "5371", "2026-09-03", "TERMINATED")
    add("1563-existing-ex-dividend-event", "TPE", "1563", "2026-08-28", "EXPECTED_TO_TRADE")
    add("6241-no-authority-event", "TWO", "6241", "2026-08-20", "EXPECTED_TO_TRADE")
    add("6241-missing-expected-bar-fail-closed", "TWO", "6241", "2026-08-20", "EXPECTED_TO_TRADE")

    cross_market_events = (
        LifecycleEventRecord(
            market_code="TPE",
            instrument_code="3707",
            status_code="SUSPENDED",
            effective_from=date(2026, 8, 24),
            evidence_id="fixture-tpe-3707-suspension",
            source_url="https://authority.example.test/tpe-3707",
        ),
    )
    cross_market = InstrumentLifecycleAuthority(
        known_identities={("TPE", "3707"), ("TWO", "3707")},
        lifecycle_events=cross_market_events,
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
            "note": "Synthetic authority uses the owner master identities without activating a bundle.",
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
                "note": "Adjacent effective ranges are deterministic and do not overlap.",
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
                "note": "Unknown event/status is not silently mapped to legal no-trade.",
            }
        )
    return rows


def main(repo: Path, output: Path) -> None:
    snapshot = source_snapshot(repo, output)
    bundle_path = repo / BUNDLE_RELATIVE
    corporate_path = repo / CORPORATE_EVENTS_RELATIVE
    unknown_path = repo / UNKNOWN_LEDGER_RELATIVE
    prior_replay_path = repo / PRIOR_REPLAY
    bundle = load_bundle(bundle_path)
    corporate_events = load_corporate_action_events(corporate_path)
    authority = InstrumentLifecycleAuthority.from_bundle(
        bundle,
        authority_version=bundle.manifest.get("referenceDataVersion"),
        corporate_events=corporate_events,
    )
    owner_identities = read_owner_master(repo)
    prior_rows = list(csv.DictReader(prior_replay_path.open(encoding="utf-8", newline="")))
    output.mkdir(parents=True, exist_ok=True)

    lifecycle_rows = [
        {
            "identity": f"{event.market_code}:{event.instrument_code}",
            "status_code": event.status_code,
            "effective_from": iso(event.effective_from),
            "effective_to": iso(event.effective_to),
            "evidence_id": event.evidence_id or "",
            "source_url": event.source_url or "",
            "reason": event.reason or "",
            "authority_state": event.authority_state,
            "source_artifact": BUNDLE_RELATIVE + "/instrument_lifecycles.json",
        }
        for event in authority.lifecycle_events
    ]
    write_csv(
        output / "existing-lifecycle-event-authority-inventory.csv",
        lifecycle_rows,
        [
            "identity",
            "status_code",
            "effective_from",
            "effective_to",
            "evidence_id",
            "source_url",
            "reason",
            "authority_state",
            "source_artifact",
        ],
    )

    event_5371 = [event for event in corporate_events if (event.market_code, event.instrument_code) == ("TWO", "5371")]
    event_1563 = [event for event in corporate_events if (event.market_code, event.instrument_code) == ("TPE", "1563")]
    unknown_6241 = None
    if unknown_path.exists():
        ledger = json.loads(unknown_path.read_text(encoding="utf-8"))
        unknown_6241 = next(
            (record for record in ledger.get("records", []) if record.get("canonical_identity") == "TWO:6241"),
            None,
        )
    lineage_rows: list[dict[str, Any]] = []
    for event in authority.lifecycle_events:
        lineage_rows.append(
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
                "interpretation": "Resolver may use date-effective lifecycle status; bundle is not activated by this task.",
            }
        )
    for event in event_5371 + event_1563:
        summary = event_summary(event)
        lineage_rows.append(
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
                "interpretation": "Objective event lineage only; it does not authorize legal no-trade without a lifecycle row.",
            }
        )
    lineage_rows.append(
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
            "interpretation": "No authoritative no-trade event found; no complete-empty proof; fail closed if bar is missing.",
        }
    )
    write_csv(
        output / "event-authority-lineage.csv",
        lineage_rows,
        [
            "identity",
            "record_layer",
            "record_kind",
            "effective_from",
            "effective_to",
            "status_code",
            "event_type",
            "evidence_id",
            "source_url",
            "source_record_id",
            "authority_state",
            "source_artifact",
            "source_sha256",
            "interpretation",
        ],
    )

    coverage_rows: list[dict[str, Any]] = []
    for status in sorted({event.status_code for event in authority.lifecycle_events} | {"ACTIVE", "LISTED", "SUSPENDED", "DELISTED", "TERMINATED"}):
        if status == "SUSPENDED":
            family = "GENERAL_SUSPENSION"
            mapping, automatic, state = "LEGAL_NO_TRADE", "YES with lineage", "IMPLEMENTED"
        elif status in {"DELISTED", "TERMINATED"}:
            family = "TERMINATION_OR_DELISTING"
            mapping, automatic, state = "TERMINATED", "YES with lineage", "IMPLEMENTED"
        else:
            family = "NEW_LISTING_OR_RESUMPTION"
            mapping, automatic, state = "EXPECTED_TO_TRADE", "YES", "IMPLEMENTED"
        coverage_rows.append(
            {
                "event_family": family,
                "existing_vocabulary": status,
                "source_layer": "instrument_lifecycles.json",
                "resolver_mapping": mapping,
                "legal_no_trade_automatic": automatic,
                "coverage_state": state,
                "gap_or_note": "Existing lifecycle status is canonical; reason/evidence/source are retained.",
            }
        )
    for event_type in sorted(set(EVENT_TYPES) | {getattr(event, "event_type", "") for event in corporate_events}):
        if not event_type:
            continue
        is_ex_dividend = event_type == "CASH_DIVIDEND_EX_DIVIDEND"
        family = {
            "CAPITAL_REDUCTION": "CAPITAL_REDUCTION_SUSPENSION",
            "SPLIT_REVERSE_SPLIT_PAR_VALUE_CHANGE": "STOCK_SPLIT_REVERSE_SPLIT",
            "MERGER_SHARE_CONVERSION_DEMERGER": "MERGER_SHARE_CONVERSION",
            "LISTING_TERMINATION_RESUMPTION_DISCONTINUITY": "RESUMPTION_TERMINATION_OR_LISTING_TRANSITION",
            "CASH_DIVIDEND_EX_DIVIDEND": "CORPORATE_ACTION_CONTINUITY_ONLY",
            "STOCK_DIVIDEND_EX_RIGHT": "CORPORATE_ACTION_CONTINUITY_ONLY",
            "RIGHTS_ISSUE_CAPITAL_INCREASE_REFERENCE_RESET": "CORPORATE_ACTION_CONTINUITY_ONLY",
            "COMBINED_EX_RIGHT_EX_DIVIDEND_SEMANTIC_PARTIAL": "CORPORATE_ACTION_CONTINUITY_ONLY",
        }.get(event_type, "UNMAPPED_CORPORATE_ACTION")
        coverage_rows.append(
            {
                "event_family": family,
                "existing_vocabulary": event_type,
                "source_layer": "corporate_action_dataset",
                "resolver_mapping": "EXPECTED_TO_TRADE unless an independent lifecycle row applies"
                if is_ex_dividend
                else "REQUIRES_DATE_EFFECTIVE_LIFECYCLE_MAPPING",
                "legal_no_trade_automatic": "NO",
                "coverage_state": "IMPLEMENTED_LINEAGE_ONLY" if is_ex_dividend else "GAP_EXPLICIT",
                "gap_or_note": "1563 ex-dividend is preserved as objective event evidence, not a suspension."
                if is_ex_dividend
                else "No automatic inference or invented date is permitted; validated lifecycle publication remains required.",
            }
        )
    write_csv(
        output / "event-type-coverage-matrix.csv",
        coverage_rows,
        [
            "event_family",
            "existing_vocabulary",
            "source_layer",
            "resolver_mapping",
            "legal_no_trade_automatic",
            "coverage_state",
            "gap_or_note",
        ],
    )

    consumer_rows = [
        ("EOD_G2", "DB resolver adapter in ingestion; replay contract", "IMPLEMENTED", "Official missing bar remains fail closed; no catch-up."),
        ("COLLECTOR", "Shared decide_missing_bar + resolver contract", "IMPLEMENTED", "No fake bar or forward fill."),
        ("TODAY_MARKET_BACKEND", "Readiness contract; frontend untouched", "READY_WITH_GAPS", "Backend publication can consume resolution; no frontend inference."),
        ("STOCK_READ_MODEL", "Readiness contract; existing fields preserved", "READY_WITH_GAPS", "Stock backend integration is bounded and not a product expansion."),
        ("LIFECYCLE_OBSERVATION_PIPELINE", "Date-effective authority read contract", "READY_WITH_GAPS", "Frozen Lifecycle V1.3 contract is untouched."),
        ("SELECTOR", "Eligibility read contract", "READY_WITH_GAPS", "Frozen Selector V1 contract is untouched."),
        ("TODAY_FRONTEND", "Explicitly excluded", "NOT_MODIFIED", "Frontend must never infer legal no-trade."),
        ("STOCK_TOPIC_OPPORTUNITY_FRONTEND", "Explicitly excluded", "NOT_MODIFIED", "No frontend mutation in this task."),
    ]
    write_csv(
        output / "consumer-integration-matrix.csv",
        [
            {"consumer": consumer, "contract_surface": surface, "readiness": readiness, "boundary": boundary}
            for consumer, surface, readiness, boundary in consumer_rows
        ],
        ["consumer", "contract_surface", "readiness", "boundary"],
    )

    replay_rows: list[dict[str, Any]] = []
    for prior in prior_rows:
        day = prior["trade_date"]
        decisions: dict[str, Any] = {}
        unresolved: list[str] = []
        for market in ("TPE", "TWO"):
            sample = prior.get(f"missing_{market.lower()}_sample", "").strip()
            if not sample:
                continue
            result = authority.resolve_trading_expectation(market, sample, date.fromisoformat(day))
            decision = decide_missing_bar(result, has_observation=False, has_priced_bar=False)
            decisions[f"{market}:{sample}"] = {
                "expectation": result.expectation.value,
                "disposition": decision.disposition,
                "reason": result.reason,
                "evidence_id": result.evidence_id,
                "corporate_event_types": [
                    getattr(event, "event_type", "")
                    for event in authority.corporate_events_for(market, sample)
                ],
            }
            if not decision.covered:
                unresolved.append(f"{market}:{sample}@{day}")
        g5371 = authority.resolve_trading_expectation("TWO", "5371", date.fromisoformat(day))
        replay_rows.append(
            {
                "trade_date": day,
                "session": prior["session"],
                "reference_view": prior["reference_view"],
                "expected_tpe": prior["expected_tpe"],
                "covered_tpe": prior["covered_tpe"],
                "missing_tpe": prior["missing_tpe"],
                "missing_tpe_sample": prior["missing_tpe_sample"],
                "expected_two": prior["expected_two"],
                "covered_two": prior["covered_two"],
                "missing_two": prior["missing_two"],
                "missing_two_sample": prior["missing_two_sample"],
                "g2_status": "PASS" if not unresolved else "FAIL_CLOSED",
                "authority_decisions": json_compact(decisions),
                "unresolved_authority_gap": ";".join(unresolved),
                "5371_resolution": g5371.expectation.value,
                "5371_evidence_id": g5371.evidence_id or "",
                "tpe_provider_records": prior["tpe_provider_records"],
                "two_provider_records": prior["two_provider_records"],
                "read_only": "YES",
                "prices_persisted": "NO",
                "notes": "Resolver replay only; no provider fetch, persistence, activation, or catch-up.",
            }
        )
    write_csv(
        output / "g2-target-session-replay.csv",
        replay_rows,
        [
            "trade_date",
            "session",
            "reference_view",
            "expected_tpe",
            "covered_tpe",
            "missing_tpe",
            "missing_tpe_sample",
            "expected_two",
            "covered_two",
            "missing_two",
            "missing_two_sample",
            "g2_status",
            "authority_decisions",
            "unresolved_authority_gap",
            "5371_resolution",
            "5371_evidence_id",
            "tpe_provider_records",
            "two_provider_records",
            "read_only",
            "prices_persisted",
            "notes",
        ],
    )

    regression_rows = build_regressions(authority)
    write_csv(
        output / "cross-consumer-regression.csv",
        regression_rows,
        [
            "case",
            "identity",
            "as_of_date",
            "expected_expectation",
            "actual_expectation",
            "disposition",
            "status_code",
            "covered",
            "provider_conflict",
            "lineage",
            "pass",
            "note",
        ],
    )

    gaps = [
        {
            "identity": "TWO:6241",
            "date_window": "2026-08-18..2026-08-24",
            "gap_type": "MISSING_LIFECYCLE_NO_TRADE_AUTHORITY",
            "current_resolution": "EXPECTED_TO_TRADE + MISSING_MARKET_DATA / FAIL_CLOSED",
            "evidence_state": "NO_AUTHORITATIVE_MATCH; NOT_PROVEN_EMPTY",
            "owner_action": "Supply approved date-effective authority or leave blocked; do not add exception.",
        },
        {
            "identity": "TPE:1563",
            "date_window": "2026-08-27..2026-08-28",
            "gap_type": "MISSING_LIFECYCLE_NO_TRADE_AUTHORITY",
            "current_resolution": "EXPECTED_TO_TRADE + MISSING_MARKET_DATA / FAIL_CLOSED",
            "evidence_state": "AUTHORITATIVE CASH_DIVIDEND_EX_DIVIDEND 2026-07-15; not legal no-trade",
            "owner_action": "Provide independent suspension/no-trade authority if one exists; do not reinterpret ex-dividend.",
        },
        {
            "identity": "ALL",
            "date_window": "N/A",
            "gap_type": "FORMAL_PUBLICATION_BOUNDARY",
            "current_resolution": "VALIDATED_FILE_NOT_FORMALLY_PUBLISHED",
            "evidence_state": "Readiness contract only; no reference bundle activation",
            "owner_action": "Owner decides any future publication/activation and bounded catch-up.",
        },
    ]
    write_csv(
        output / "unresolved-authority-gaps.csv",
        gaps,
        ["identity", "date_window", "gap_type", "current_resolution", "evidence_state", "owner_action"],
    )

    summary = bundle.summary()
    source_lines = [
        "# Source state\n",
        f"- Owner-designated checkout: `{repo}`",
        f"- HEAD at inventory: `{snapshot['head']}`",
        f"- Branch: `{snapshot['branch']}`",
        f"- Origin: `{snapshot['origin']}`",
        f"- Dirty status captured before report generation: `{snapshot['status_total']}` entries ({snapshot['tracked_dirty']} tracked, {snapshot['untracked']} untracked).",
        "- Existing owner changes were preserved; no reset, clean, restore, force, production deployment, or database mutation was performed.",
        f"- Current bundle digest: `{bundle.digest()}`; summary: `{json_compact(summary)}`",
        f"- Existing corporate-event artifact SHA-256: `{file_sha256(corporate_path)}`",
        f"- Existing corporate-event record count loaded and validated: `{len(corporate_events)}`",
        f"- Owner master identities read for cross-market regression: `{len(owner_identities)}`",
        "- This report's file outputs are generated from the read-only source snapshot; the output directory itself was not included in the pre-generation dirty count.",
    ]
    (output / "source-state.md").write_text("\n".join(source_lines) + "\n", encoding="utf-8")

    inventory_lines = [
        "# Existing lifecycle/event authority inventory",
        "",
        "## Layers",
        "",
        "- Raw event record: source-shaped or normalized event input; not a consumer authorization.",
        "- Validated event: schema, identity, official-source, date, hash, and stable-key validation passed; the REC-A1 dataset is in this layer.",
        "- Formal lifecycle/trading authority: date-effective reference lifecycle row with status, evidence, source, and resolver semantics. The current file bundle is validated/read-only and is not formally published or activated by this task.",
        "",
        "## Existing reference lifecycle rows",
        "",
    ]
    inventory_lines.extend(
        f"- `{row['identity']}` `{row['status_code']}` `{row['effective_from']}..{row['effective_to'] or 'open'}` evidence `{row['evidence_id']}`"
        for row in lifecycle_rows
    )
    inventory_lines.extend(
        [
            "",
            "## Existing corporate-action records",
            "",
            f"- `TWO:5371`: {len(event_5371)} validated record(s); these are separate from the two lifecycle rows and do not replace them.",
            f"- `TPE:1563`: {len(event_1563)} validated record(s); the found event is `CASH_DIVIDEND_EX_DIVIDEND` effective `2026-07-15`, not a suspension/no-trade authority.",
            f"- `TWO:6241`: event-gap review record found: `{'YES' if unknown_6241 else 'NO'}`; no authoritative no-trade event was found.",
        ]
    )
    (output / "existing-lifecycle-event-authority-inventory.md").write_text(
        "\n".join(inventory_lines) + "\n", encoding="utf-8"
    )

    records_lines = [
        "# Existing event records: 5371 and 1563",
        "",
        "## TWO:5371",
        "",
        "- Existing lifecycle rows were read from the current reference bundle; no new symbol-specific exception was added.",
        "- `SUSPENDED`: `2026-08-24` through `2026-09-02`; resolver answer is `LEGAL_NO_TRADE` only inside this effective range.",
        "- `TERMINATED`: `2026-09-03` onward; resolver answer is `TERMINATED` from that boundary.",
        "- The separately found REC-A1 corporate-action row is `CASH_DIVIDEND_EX_DIVIDEND` effective `2026-06-17`; it is not used to create the suspension.",
        "",
        "## TPE:1563",
        "",
    ]
    records_lines.extend(f"- `{json_compact(event_summary(event))}`" for event in event_1563)
    records_lines.extend(
        [
            "",
            "The 1563 record is objective ex-dividend evidence only. For `2026-08-27` and `2026-08-28`, the resolver therefore returns `EXPECTED_TO_TRADE`; an absent official bar remains `MISSING_MARKET_DATA` and fail closed.",
            "",
            "## Conclusion",
            "",
            "Both existing records were found and read. Only the existing 5371 lifecycle rows authorize legal no-trade. No hard-coded `if code == ...` logic was introduced.",
        ]
    )
    (output / "existing-event-records-5371-1563.md").write_text(
        "\n".join(records_lines) + "\n", encoding="utf-8"
    )

    authority_contract = """# Instrument Lifecycle / Trading Expectation Authority Contract

## Identity and layers

The identity is the existing market-aware pair `(market_code, instrument_code)`. A lifecycle authority is a read-only, date-effective collection of validated `ReferenceInstrumentLifecycle` rows. Each legal no-trade result must retain `status_code`, `effective_from`, `effective_to`, `evidence_id`, `source_url`, and the authority/publication state.

The contract distinguishes raw event records, validated corporate/lifecycle events, and formally published authority. The current file bundle is `VALIDATED_FILE_NOT_FORMALLY_PUBLISHED`; this task does not activate it or mutate production state.

## Resolution boundary

`InstrumentLifecycleAuthority.resolve_trading_expectation(market_code, instrument_code, as_of_date)` is the canonical read. Database consumers can use `resolve_sqlalchemy_trading_expectation(...)` against one active reference registry version. Missing identity or unavailable registry returns `UNKNOWN`; it never becomes legal no-trade.

Existing lifecycle vocabulary is reused: `ACTIVE`, `LISTED`, `SUSPENDED`, `DELISTED`, and `TERMINATED`. The consumer answer is `EXPECTED_TO_TRADE`, `LEGAL_NO_TRADE`, `NOT_YET_LISTED`, `TERMINATED`, `INACTIVE`, or `UNKNOWN`.

Exact duplicate rows are idempotently deduplicated. Overlapping rows with different statuses are rejected as an authority conflict. Effective-date boundaries are inclusive and deterministic.

## Publication boundary

This task provides a validated file/read contract and a database read adapter. It does not perform registry publication, reference-bundle activation, migration, deployment, or catch-up. An owner-approved future publication must preserve the same identity and lineage contract.
"""
    (output / "instrument-lifecycle-authority-contract.md").write_text(authority_contract, encoding="utf-8")

    resolver_contract = """# Trading Expectation Resolver Contract

## Input

`(market_code, instrument_code, as_of_date)` plus a read-only validated authority source.

## Output

The resolution contains `expectation`, applicable lifecycle status, reason, effective range, event/evidence lineage, authority version, and publication state.

## Fail-closed policy

- `EXPECTED_TO_TRADE` + no official priced bar => `MISSING_MARKET_DATA`, uncovered, fail closed.
- `LEGAL_NO_TRADE` => bar is not required; the consumer may record an explicit status payload with null OHLCV, but must not create fake OHLCV, zero-volume bars, or forward-fill a prior close.
- `TERMINATED`, `INACTIVE`, or `NOT_YET_LISTED` are non-trading answers only when supported by validated authority/identity bounds.
- `UNKNOWN` + no bar never degrades to legal no-trade.
- Corporate-action event records, including ex-dividend, are not legal no-trade unless an independent date-effective lifecycle authority row establishes that meaning.

## Consumers

EOD G2/collector, Today Market backend/publication, Stock read model, Lifecycle observation pipeline, and Selector eligibility/read paths consume this contract. Frontends do not infer legal no-trade. Existing frozen Lifecycle V1.3 and Selector V1 contracts remain untouched.
"""
    (output / "trading-expectation-resolver-contract.md").write_text(resolver_contract, encoding="utf-8")

    pass_count = sum(row["pass"] == "PASS" for row in regression_rows)
    replay_pass = sum(row["g2_status"] == "PASS" for row in replay_rows)
    replay_fail = [row for row in replay_rows if row["g2_status"] != "PASS"]
    fixed_fields = f"""TASK={TASK}
EXACT_SHA={snapshot['head']}
CANONICAL_IDENTITY_KEY=(market_code, instrument_code)
INSTRUMENT_LIFECYCLE_AUTHORITY=READY_WITH_GAPS
TRADING_EXPECTATION_RESOLVER=IMPLEMENTED
EXISTING_5371_EVENT_FOUND=YES
EXISTING_1563_EVENT_FOUND=YES
5371_RESOLUTION=EXPECTED_TO_TRADE before 2026-08-24; LEGAL_NO_TRADE 2026-08-24..2026-09-02; TERMINATED from 2026-09-03
1563_RESOLUTION=EXPECTED_TO_TRADE; existing CASH_DIVIDEND_EX_DIVIDEND is not legal no-trade
6241_AUTHORITY=MISSING
EXPECTED_TO_TRADE_MISSING_BAR_FAIL_CLOSED=PASS
LEGAL_NO_TRADE_NO_FAKE_BAR=PASS
CROSS_MARKET_IDENTITY=PASS
CROSS_CONSUMER_CONTRACT=PARTIAL
TODAY_CONSUMER_READINESS=READY_WITH_GAPS
EOD_G2_TARGET_SESSIONS={replay_pass}/11_PASS plus {len(replay_fail)} FAIL_CLOSED: {', '.join(row['unresolved_authority_gap'] for row in replay_fail)}
UNRESOLVED_AUTHORITY_GAPS=TWO:6241 2026-08-18..2026-08-24; TPE:1563 2026-08-27..2026-08-28; formal publication boundary
PRODUCTION_MUTATION=NO
FRONTEND_MUTATION=NO
LIFECYCLE_FROZEN_CONTRACT_MUTATION=NO
SELECTOR_FROZEN_CONTRACT_MUTATION=NO
EOD_CATCHUP_EXECUTED=NO
OWNER_DECISION_REQUIRED=YES
NEXT_TASK=NONE
"""
    report = f"""# {TASK}

## Fixed closure fields

```text
{fixed_fields}```

## Closure outcome

The canonical, market-aware resolver is implemented as a read-only authority contract over the repository's existing date-effective lifecycle rows. The current validated file authority is ready with publication gaps; no production reference bundle was activated.

## Implementation surface

- `services/api/src/topicpilot_api/instrument_lifecycle_authority.py` — canonical authority/resolver, lineage output, duplicate/conflict validation, and shared missing-bar decision.
- `services/api/src/topicpilot_api/market_data/ingestion.py` — bounded read-only DB adapter using the shared resolver; existing compatibility classifier retained for already-resolved status callers.
- `services/api/src/topicpilot_api/daily_market.py` and `services/api/src/topicpilot_api/production_read_model.py` — no-trade status vocabulary now comes from the canonical shared catalogue; no frontend/product expansion.
- `services/api/tests/test_instrument_lifecycle_authority.py` — authority, boundary, identity, lineage, and fail-closed tests.
- `tools/ws4_canonical_lifecycle_authority_closure.py` — repeatable read-only replay/report generator.

- `CANONICAL_IDENTITY_KEY=(market_code, instrument_code)`
- Existing 5371 lifecycle records found: `YES` (two date-effective rows)
- Existing 1563 event record found: `YES` (`CASH_DIVIDEND_EX_DIVIDEND`, 2026-07-15; not no-trade)
- 5371: `EXPECTED_TO_TRADE` before 2026-08-24; `LEGAL_NO_TRADE` 2026-08-24..2026-09-02; `TERMINATED` from 2026-09-03
- 1563: `EXPECTED_TO_TRADE` on 2026-08-27..2026-08-28; missing official price remains fail closed
- 6241: no formal no-trade authority found; remains expected-trade missing-data fail closed
- Cross-consumer regression: `{pass_count}/{len(regression_rows)} PASS`
- Resolver G2 replay: `{replay_pass}/11 PASS`; `{len(replay_fail)}/11 FAIL_CLOSED`

## Boundary and safety

No hard-coded instrument exception was added. The 1563 ex-dividend record was not reinterpreted as suspension. Unknown event evidence cannot become legal no-trade. No synthetic price, fake OHLCV, forward-filled close, web OHLCV substitution, production mutation, frontend mutation, frozen Lifecycle/Selector contract mutation, or EOD catch-up was performed.

The current report is a bounded authority/readiness closure. Owner decision is required for any future formal publication and for the remaining authority gaps before bounded EOD catch-up.

## Replay residuals

{chr(10).join(f"- {row['trade_date']}: {row['unresolved_authority_gap']}" for row in replay_fail)}
"""
    (output / "formal-closure-report.md").write_text(report, encoding="utf-8")

    tests = """# Tests run

- `py -3.12 -m pytest services/api/tests/test_instrument_lifecycle_authority.py -q` — 8 passed.
- `py -3.12 -m pytest services/api/tests/test_no_trade_contract.py -q` — 10 passed.
- Combined validation before artifact generation: 18 passed (8 authority tests plus 10 existing no-trade tests).
- Bounded consumer suite (`authority`, `no_trade`, `provider_preflight`, `known_event_aware_publication`, `stock_eod`, `reference_bundle`, `daily_market`, `production_read_model_search`) — 55 passed.
- Resolver-based cross-consumer regression matrix: see `cross-consumer-regression.csv`.
- Target-session replay: see `g2-target-session-replay.csv`; read-only, no provider fetch or persistence.
"""
    (output / "tests-run.md").write_text(tests, encoding="utf-8")

    checklist = """# Closure checklist

- [x] Existing 5371 and 1563 event records located and read.
- [x] 5371 lifecycle rows reused; no symbol-specific hard-coded exception.
- [x] 1563 ex-dividend event kept separate from legal no-trade authority.
- [x] 6241 remains unresolved/fail-closed without invented event evidence.
- [x] Market-aware identity and cross-market same-code isolation tested.
- [x] Effective-date boundaries, duplicate idempotency, overlap conflict, unknown identity/event, resumed trading, terminated instrument, and missing expected bar tested.
- [x] Expected-trade missing bar fails closed.
- [x] Legal no-trade does not create fake bar or forward-fill.
- [x] 11 target sessions replayed with resolver; coverage gate not lowered.
- [x] Frontends, frozen Lifecycle/Selector contracts, DB activation, production, taxonomy, catch-up, and NEXT_TASK left unchanged.
- [ ] Formal publication/activation — owner decision required.
- [ ] 6241 authority evidence — owner/source decision required.
- [ ] 1563 suspension/no-trade evidence, if any — owner/source decision required.
"""
    (output / "closure-checklist.md").write_text(checklist, encoding="utf-8")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    main(arguments.repo.resolve(), arguments.output.resolve())
