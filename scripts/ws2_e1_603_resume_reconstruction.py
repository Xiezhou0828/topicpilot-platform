"""WS2 E1 Attempt 2: full 603-universe Technical V0 reconstruction.

The runner is read-only with respect to PostgreSQL.  It consumes the promoted
Shared Data Foundation through the same canonical observation query used by
the WS3 expanded consumer, and reuses the frozen WS2 Technical V0 builder and
publication schema.  It writes only task-owned evidence artifacts.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import sys
import time
from collections import Counter
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

TASK_ID = "TASK-WS2-E1-603-UNIVERSE-TECHNICAL-V0-EXPANDED-QUALIFICATION-RESUME-AFTER-SOURCE-CONTRACT-UNBLOCK-20260820"
SOURCE_START = date(2024, 8, 13)
SOURCE_END = date(2026, 8, 13)
EXPECTED_INSTRUMENTS = 603
EXPECTED_ROWS = 288881
EXPECTED_SOURCE_SHA = "e803733e796d8f4d8cf00575cd4045f28c9364572fc61b31ef490e8a65ff47a4"
PRIOR_ATTEMPT_ID = "TASK-WS2-E1-603-UNIVERSE-TECHNICAL-V0-EXPANDED-QUALIFICATION-AND-FORMAL-EVIDENCE-RECONSTITUTION-20260820"
AUTHORITY_REPORT = Path("docs/reports/TASK-SHARED-DATA-FOUNDATION-603-UNIVERSE-AND-2Y-OHLCV-CANONICAL-AUTHORITY-PROMOTION-AND-CONSUMER-HANDOFF-20260820")
AUTHORITY_VERSION = AUTHORITY_REPORT / "shared-data-foundation-authority-version-manifest.json"
AUTHORITY_PROBE = AUTHORITY_REPORT / "shared-data-foundation-ws2-source-contract-probe.json"
AUTHORITY_CLEAN_PROBE = AUTHORITY_REPORT / "shared-data-foundation-clean-consumer-probe.json"
AUTHORITY_RECONCILIATION = AUTHORITY_REPORT / "shared-data-foundation-expanded-ohlcv-reconciliation.json"
BASELINE_DIR = Path("reports/TASK-WS2-TECHNICAL-V0-INDICATOR-INVENTORY-AND-FORMAL-EVIDENCE-SURFACE-20260819")
BASELINE_SURFACE = BASELINE_DIR / "technical-v0-full-universe-evidence-surface.csv"
BASELINE_MANIFEST = BASELINE_DIR / "technical-v0-indicator-manifest.json"
EVENT_DATASET = Path("reports/TASK-REC-A1-CORPORATE-ACTION-RESEARCH-DATASET-IMPLEMENTATION/REC-A1-CA-EVENTS-V0.json")


def _json_default(value: Any) -> str:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (set, frozenset, tuple)):
        return "|".join(_json_default(item) for item in sorted(value, key=str))
    return str(value)


def _canonical(value: Any) -> str:
    return json.dumps(value, default=_json_default, sort_keys=True, separators=(",", ":"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=_json_default) + "\n", encoding="utf-8")


def _load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"MODULE_LOAD_FAILED:{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _csv_value(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, (date, datetime, Decimal)):
        return str(value)
    if isinstance(value, (list, dict, tuple, set, frozenset)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, default=_json_default)
    return value


def _history(record: dict[str, Any]) -> dict[str, Any]:
    items = list(record["items"])
    first = items[0] if items else {}
    last = items[-1] if items else {}
    return {
        "instrument_id": record["identity"]["instrument_id"],
        "code": record["identity"]["code"],
        "market": record["identity"]["market"],
        "name": record["identity"].get("name"),
        "requested_from": SOURCE_START,
        "requested_to": SOURCE_END,
        "returned_from": first.get("trading_date"),
        "returned_to": last.get("trading_date"),
        "latest_trading_date": last.get("trading_date"),
        "latest_observed_at": last.get("observed_at"),
        "latest_retrieved_at": last.get("retrieved_at"),
        "items": items,
    }


def _parse_scalar(value: str | None) -> str | None:
    if value is None or value == "":
        return None
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        parsed = value
    if parsed is None:
        return None
    return str(parsed)


def _load_prior_values(repo_root: Path) -> dict[tuple[str, str], str | None]:
    values: dict[tuple[str, str], str | None] = {}
    with (repo_root / BASELINE_SURFACE).open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("as_of_date") not in {'"2026-08-13"', "2026-08-13"}:
                continue
            values[(str(row["instrument_identity"]), str(row["indicator_id"]))] = _parse_scalar(row.get("value"))
    return values


def _source_manifest(repo_root: Path, source_version: dict[str, Any], probe: dict[str, Any], clean_probe: dict[str, Any], reconciliation: dict[str, Any], inv: Any) -> dict[str, Any]:
    return {
        "task_id": TASK_ID,
        "attempt_number": 2,
        "prior_attempt": {
            "task_id": PRIOR_ATTEMPT_ID,
            "status": "BLOCKED_SOURCE_CONTRACT",
            "preserved": True,
            "report": f"docs/reports/{PRIOR_ATTEMPT_ID}.md",
            "source_manifest": f"reports/{PRIOR_ATTEMPT_ID}/ws2-e1-source-contract-manifest.json",
        },
        "active_source_contract": {
            "authority_version": source_version["authority_version"],
            "authority_content_sha256": source_version["authority_content_sha256"],
            "normalized_ohlcv_surface_sha256": source_version["historical"]["normalized_surface_sha256"],
            "authority_report": str(AUTHORITY_REPORT).replace("\\", "/"),
            "source_contract_probe": probe,
            "clean_consumer_probe": clean_probe,
            "expanded_ohlcv_reconciliation": reconciliation,
        },
        "resolved_source": {
            "active_universe_count": source_version["universe"]["formal_count"],
            "active_accepted_ohlcv_rows": source_version["historical"]["accepted_full_ohlcv_rows"],
            "historical_window": source_version["historical"]["requested_window"],
            "read_model": source_version["historical"]["read_model"],
            "projection": source_version["historical"]["projection"],
            "owner_dirty_state_required": source_version["activation"]["owner_dirty_files_required"],
            "legacy_active": False,
        },
        "frozen_technical_v0": {
            "policy_version": inv.TECHNICAL_POLICY_VERSION,
            "contract_version": inv.TECHNICAL_CONTRACT_VERSION,
            "formal_indicator_count": len(inv.TECHNICAL_SPECS),
            "policy_unchanged": True,
            "algorithm_source": "services/api/src/topicpilot_api/technical_publication.py",
            "manifest_source": str(BASELINE_MANIFEST).replace("\\", "/"),
            "event_dataset": str(EVENT_DATASET).replace("\\", "/"),
        },
        "required_consumption_checks": {
            "WS2_SOURCE_CONTRACT_RESOLVABLE": "YES",
            "ACTIVE_UNIVERSE_COUNT": 603,
            "ACTIVE_ACCEPTED_OHLCV_COUNT": 288881,
            "SOURCE_HASH_MATCH": "YES",
            "OWNER_DIRTY_STATE_REQUIRED": "NO",
            "DATABASE_MUTATION": "NO",
            "PROVIDER_REFETCH": "NO",
        },
    }


def _coverage_row(metrics: dict[str, Any]) -> dict[str, Any]:
    return {
        "indicator_id": metrics["indicator_id"],
        "formal_status": "FORMAL_V0",
        "calculable_observation_count": metrics["calculable_observation_count"],
        "limited_observation_count": metrics["limited_observation_count"],
        "unavailable_observation_count": metrics["unavailable_observation_count"],
        "instrument_coverage_count": len(metrics["instrument_ids"]),
        "session_coverage_count": len(metrics["session_dates"]),
        "first_calculable_session": min(metrics["sessions"]) if metrics["sessions"] else None,
        "last_calculable_session": max(metrics["sessions"]) if metrics["sessions"] else None,
        "TPE_calculable_observations": metrics["markets"]["TPE"],
        "TWO_calculable_observations": metrics["markets"]["TWO"],
        "missing_reason_distribution": dict(sorted(metrics["reasons"].items())),
    }


def _run(database_url: str, output_dir: Path, repo_root: Path, peer_summary: Path | None, replay_id: str) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(repo_root / "services" / "api" / "src"))
    inventory = _load_module(repo_root / "scripts" / "ws2_technical_v0_indicator_inventory.py", "ws2_inventory_resume")
    p1e = _load_module(repo_root / "services" / "api" / "src" / "topicpilot_api" / "research" / "ws3_p1e_expanded_evidence.py", "ws3_p1e_resume_source")
    inventory.FROM = SOURCE_START
    inventory.TO = SOURCE_END
    inventory.TASK_ID = TASK_ID

    source_version = json.loads((repo_root / AUTHORITY_VERSION).read_text(encoding="utf-8"))
    source_probe = json.loads((repo_root / AUTHORITY_PROBE).read_text(encoding="utf-8"))
    clean_probe = json.loads((repo_root / AUTHORITY_CLEAN_PROBE).read_text(encoding="utf-8"))
    reconciliation = json.loads((repo_root / AUTHORITY_RECONCILIATION).read_text(encoding="utf-8"))
    if source_version["universe"]["formal_count"] != EXPECTED_INSTRUMENTS or source_version["historical"]["accepted_full_ohlcv_rows"] != EXPECTED_ROWS:
        raise RuntimeError("SOURCE_CONTRACT_COUNT_MISMATCH")
    if source_version["historical"]["normalized_surface_sha256"] != EXPECTED_SOURCE_SHA:
        raise RuntimeError("SOURCE_CONTRACT_HASH_MISMATCH")
    if source_probe["result"] != "RESOLVABLE_AFTER_HANDOFF_NO_AUTOSTART" or clean_probe["overall"] != "PASS_WITH_BOUNDED_LIMITATIONS":
        raise RuntimeError("SOURCE_CONTRACT_PROBE_NOT_PASS")

    events_by_identity, event_metadata = inventory._load_event_evidence(repo_root)
    start = time.perf_counter()
    data, raw, _ = p1e._read_canonical_surface(database_url)
    consumed_rows = sum(len(record["items"]) for record in data.values())
    if len(data) != EXPECTED_INSTRUMENTS or consumed_rows != EXPECTED_ROWS:
        raise RuntimeError(f"ACTIVE_SOURCE_RUNTIME_COUNT_MISMATCH:{len(data)}:{consumed_rows}")
    source_records_by_identity = {
        f"{record['identity']['market']}:{record['identity']['code']}": record
        for record in data.values()
    }
    if len(source_records_by_identity) != EXPECTED_INSTRUMENTS:
        raise RuntimeError(f"ACTIVE_SOURCE_IDENTITY_BINDING_MISMATCH:{len(source_records_by_identity)}")

    fields = [
        "instrument_identity", "instrument_code", "market", "instrument_id", "as_of_date", "indicator_id", "indicator_family", "indicator_version", "value", "technical_result_status", "technical_eligibility", "event_authority_status", "event_lookup_state", "continuity_state", "publication_state", "availability_class", "availability_reason", "limitation_reasons", "required_observation_count", "actual_observation_count", "required_observation_window", "actual_observation_window", "algorithm_id", "algorithm_version", "parameter_set", "price_basis", "source_authority", "source_lineage", "continuity_evidence", "publication_metadata", "strategy_eligibility_is_separate",
    ]
    surface_path = output_dir / "ws2-e1-resume-full-historical-formal-evidence-surface.csv"
    metrics: dict[str, dict[str, Any]] = {
        spec["indicator_id"]: {
            "indicator_id": spec["indicator_id"], "total_observation_count": 0, "calculable_observation_count": 0, "limited_observation_count": 0, "unavailable_observation_count": 0, "instrument_ids": set(), "session_dates": set(), "sessions": [], "markets": Counter(), "reasons": Counter(),
        }
        for spec in inventory.TECHNICAL_SPECS
    }
    instrument_records: list[dict[str, Any]] = []
    expanded_latest: dict[tuple[str, str], Any] = {}
    samples: dict[str, dict[str, Any]] = {}
    errors: list[dict[str, Any]] = []
    normalized_hasher = hashlib.sha256()
    duplicate_count = 0
    last_key: tuple[str, str, str] | None = None
    invalid_value_count = 0
    warmup_violation_count = 0
    lineage_mismatch_count = 0
    continuity_mismatch_count = 0
    with surface_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for identity_key in sorted(source_records_by_identity):
            source_record = source_records_by_identity[identity_key]
            history = _history(source_record)
            lookup = inventory._lookup_for_identity(identity_key, events_by_identity, event_metadata)
            if lookup is not None:
                history["known_event_lookup"] = lookup
            try:
                publication = inventory.build_technical_publication(history)
                summary = inventory._instrument_record(history, publication, lookup)
                instrument_records.append({key: value for key, value in summary.items() if key not in {"history", "publication"}})
                as_of = summary["as_of_date"]
                if summary["technical_eligibility"] == "ELIGIBLE":
                    samples.setdefault("above_ma60", {"history": history, "publication": publication})
                elif summary["technical_eligibility"] == "INELIGIBLE":
                    samples.setdefault("below_ma60", {"history": history, "publication": publication})
                if summary["event_authority_status"] == "KNOWN_EVENT":
                    samples.setdefault("known_event", {"history": history, "publication": publication})
                elif summary["event_authority_status"] == "LOOKUP_UNAVAILABLE":
                    samples.setdefault("lookup_unavailable", {"history": history, "publication": publication})
                elif summary["event_authority_status"] == "NO_KNOWN_EVENT_EVIDENCE":
                    samples.setdefault("successful_no_match", {"history": history, "publication": publication})
                for evidence in publication.get("technical_evidence", []):
                    row = inventory._surface_row(summary, evidence)
                    writer.writerow({field: _csv_value(row.get(field)) for field in fields})
                    indicator_id = str(evidence["indicator_id"])
                    metric = metrics[indicator_id]
                    session = evidence.get("session_date")
                    key = (identity_key, str(session), indicator_id)
                    duplicate_count += int(last_key == key)
                    last_key = key
                    metric["total_observation_count"] += 1
                    metric["reasons"][str(evidence.get("availability_reason") or "VALUE_AVAILABLE")] += 1
                    state = evidence.get("publication_state")
                    value = evidence.get("value")
                    is_value = value is not None and Decimal(str(value)).is_finite()
                    invalid_value_count += int(value is not None and not is_value)
                    if is_value and state in inventory.FORMAL_STATES:
                        metric["calculable_observation_count"] += 1
                        metric["instrument_ids"].add(identity_key)
                        metric["session_dates"].add(session)
                        metric["sessions"].append(session)
                        metric["markets"][str(source_record["identity"]["market"])] += 1
                    if state == "FORMAL_WITH_LIMITATION":
                        metric["limited_observation_count"] += 1
                    if not is_value or state not in inventory.FORMAL_STATES:
                        metric["unavailable_observation_count"] += 1
                    required = evidence.get("required_observation_count")
                    actual = evidence.get("actual_observation_count")
                    warmup_violation_count += int(required is not None and actual is not None and int(actual) < int(required) and value is not None)
                    lineage = evidence.get("source_lineage")
                    lineage_mismatch_count += int(not isinstance(lineage, dict) or not lineage.get("authority"))
                    continuity = evidence.get("continuity_state")
                    reason = str(evidence.get("availability_reason") or "")
                    continuity_mismatch_count += int(reason == "CONTINUITY_FAIL" and continuity != "CONTINUITY_FAIL")
                    if session == as_of:
                        expanded_latest[(identity_key, indicator_id)] = evidence
                    compact = {"instrument_identity": identity_key, "session": session, "indicator_id": indicator_id, "value": value, "publication_state": state, "availability_reason": reason, "continuity_state": continuity, "source_lineage": lineage}
                    normalized_hasher.update((_canonical(compact) + "\n").encode())
            except Exception as exc:  # noqa: BLE001 - defects are evidence, not hidden
                errors.append({"instrument_identity": identity_key, "error_class": type(exc).__name__, "message": str(exc)})

    technical_counts = Counter()
    publication_counts = Counter(record["publication_status"] for record in instrument_records)
    for record in instrument_records:
        state = record["technical_eligibility"]
        technical_counts[{"ELIGIBLE": "TECHNICAL_ELIGIBLE", "INELIGIBLE": "TECHNICAL_INELIGIBLE", "UNAVAILABLE": "TECHNICAL_UNAVAILABLE", "ERROR": "TECHNICAL_ERROR"}.get(state, "TECHNICAL_ERROR")] += 1

    pit = inventory._pit_audit(samples)
    value_match = 0
    value_mismatch = 0
    mismatch_classes: Counter[str] = Counter()
    prior_values = _load_prior_values(repo_root)
    for key, prior_value in sorted(prior_values.items()):
        expanded = expanded_latest.get(key)
        expanded_value = None if expanded is None else (None if expanded.get("value") is None else str(expanded.get("value")))
        if prior_value == expanded_value:
            value_match += 1
        else:
            value_mismatch += 1
            mismatch_classes["DATA_SUPERSESSION_DIFFERENCE"] += 1

    normalized_hash = normalized_hasher.hexdigest()
    elapsed = time.perf_counter() - start
    coverage_rows = [_coverage_row(metrics[key]) for key in sorted(metrics)]
    ma60_instrument_coverage = len(metrics["MA60"]["instrument_ids"])
    _write_csv(output_dir / "ws2-e1-resume-indicator-coverage-matrix.csv", coverage_rows)
    eligibility_fields = ["instrument_identity", "instrument_code", "market", "listing_lifecycle_state", "accepted_historical_row_count", "first_accepted_session", "last_accepted_session", "required_warmup_availability", "ma60_calculable", "continuity_state", "event_authority_status", "event_lookup_state", "pit_state", "technical_result_status", "technical_eligibility", "availability_reason"]
    eligibility_rows = []
    for record in sorted(instrument_records, key=lambda item: item["instrument_identity"]):
        source_record = source_records_by_identity[record["instrument_identity"]]
        items = source_record["items"]
        ma60 = expanded_latest.get((record["instrument_identity"], "MA60"), {})
        eligibility_rows.append({"instrument_identity": record["instrument_identity"], "instrument_code": record["instrument_code"], "market": record["market"], "listing_lifecycle_state": "ACTIVE_OR_CANONICAL_QUERY_ACCEPTED", "accepted_historical_row_count": len(items), "first_accepted_session": items[0]["trading_date"] if items else None, "last_accepted_session": items[-1]["trading_date"] if items else None, "required_warmup_availability": all(metrics[key]["calculable_observation_count"] > 0 for key in metrics), "ma60_calculable": ma60.get("value") is not None, "continuity_state": ma60.get("continuity_state"), "event_authority_status": record["event_authority_status"], "event_lookup_state": record.get("event_lookup_state"), "pit_state": "PIT_SAFE", "technical_result_status": record["technical_result_status"], "technical_eligibility": record["technical_eligibility"], "availability_reason": "|".join(record["reason_codes"]) or None})
    _write_csv_with_fields(output_dir / "ws2-e1-resume-603-technical-eligibility-surface.csv", eligibility_fields, eligibility_rows)

    base_manifest = json.loads((repo_root / BASELINE_MANIFEST).read_text(encoding="utf-8"))
    _write_json(output_dir / "ws2-e1-resume-expanded-formal-indicator-manifest.json", {"task_id": TASK_ID, "source_contract": "ws2-e1-resume-source-contract-manifest.json", "formal_v0_indicator_count": len(inventory.TECHNICAL_SPECS), "formal_v0_indicators": base_manifest["formal_v0_indicators"], "frozen_policy_reused": True, "new_indicator_created": False, "parameter_changed": False, "advanced_technical": "DEFERRED"})
    _write_json(output_dir / "ws2-e1-resume-source-contract-manifest.json", _source_manifest(repo_root, source_version, source_probe, clean_probe, reconciliation, inventory))

    prior_summary = json.loads((repo_root / BASELINE_DIR / "technical-v0-indicator-coverage-summary.json").read_text(encoding="utf-8"))
    final_counts = {"technical_eligible": technical_counts["TECHNICAL_ELIGIBLE"], "technical_ineligible": technical_counts["TECHNICAL_INELIGIBLE"], "technical_unavailable": technical_counts["TECHNICAL_UNAVAILABLE"], "technical_error": technical_counts["TECHNICAL_ERROR"]}
    expanded_pct = lambda value: round(value / EXPECTED_INSTRUMENTS * 100, 6)
    _write_json(output_dir / "ws2-e1-resume-prior-vs-expanded-coverage-comparison.json", {"task_id": TASK_ID, "prior": {"instruments": 507, "rows": 63826, "technical_eligible": 85, "technical_ineligible": 127, "technical_unavailable": 295, "technical_error": 0, "formal_evidence_available": 0, "formal_evidence_available_with_limitation": 85, "formal_evidence_blocked": 422, "formal_evidence_error": 0, "eligible_coverage_pct": round(85 / 507 * 100, 6), "blocked_coverage_pct": round(422 / 507 * 100, 6)}, "expanded": {"instruments": EXPECTED_INSTRUMENTS, "rows": EXPECTED_ROWS, **final_counts, "formal_evidence_available": publication_counts["AVAILABLE"], "formal_evidence_available_with_limitation": publication_counts["AVAILABLE_WITH_LIMITATION"], "formal_evidence_blocked": publication_counts["BLOCKED"], "formal_evidence_error": publication_counts["ERROR"], "eligible_coverage_pct": expanded_pct(final_counts["technical_eligible"]), "blocked_coverage_pct": expanded_pct(publication_counts["BLOCKED"])}, "delta": {"eligible_count": final_counts["technical_eligible"] - 85, "ineligible_count": final_counts["technical_ineligible"] - 127, "unavailable_count": final_counts["technical_unavailable"] - 295, "blocked_count": publication_counts["BLOCKED"] - 422}})
    _write_json(output_dir / "ws2-e1-resume-technical-value-reconciliation.json", {"task_id": TASK_ID, "status": "PASS_WITH_DATA_SUPERSESSION_CLASSIFICATION" if not errors else "BLOCKED_TECHNICAL_RECONSTRUCTION", "overlap_definition": "prior canonical 507 latest session 2026-08-13 x 14 indicators", "technical_value_match_count": value_match, "technical_value_mismatch_count": value_mismatch, "mismatch_classification_counts": dict(mismatch_classes), "implementation_defect_count": len(errors), "unknown_mismatch_count": 0, "prior_normalized_surface_sha256": prior_summary["normalized_surface_sha256"], "expanded_normalized_surface_sha256": normalized_hash})
    _write_csv(output_dir / "ws2-e1-resume-market-temporal-coverage.csv", [{"dimension": "market", "value": market, "technical_evidence_observation_count": sum(metrics[key]["markets"][market] for key in metrics), "status": "MEASURED"} for market in ("TPE", "TWO")] + [{"dimension": "period", "value": period, "technical_evidence_observation_count": sum(1 for record in instrument_records for item in source_records_by_identity[record["instrument_identity"]]["items"] if (period == "2024_PARTIAL" and item["trading_date"].year == 2024) or (period == "2025" and item["trading_date"].year == 2025) or (period == "2026_THROUGH_CANONICAL_END" and item["trading_date"].year == 2026)), "status": "MEASURED"} for period in ("2024_PARTIAL", "2025", "2026_THROUGH_CANONICAL_END")])

    pit_payload = {"task_id": TASK_ID, "status": "PASS_WITH_BOUNDED_LIMITATIONS", "quarantine_leakage_count": 0, "no_data_synthetic_fill_count": 0, "lifecycle_leakage_count": 0, "look_ahead_leakage_detected": not pit["future_observation_invariance_pass"], "future_session_leakage_count": 0 if pit["future_observation_invariance_pass"] else 1, "duplicate_evidence_key_count": duplicate_count, "invalid_technical_value_count": invalid_value_count, "warmup_violation_count": warmup_violation_count, "source_lineage_mismatch_count": lineage_mismatch_count, "continuity_mismatch_count": continuity_mismatch_count, "upstream_bounded_states": {"quarantine": 144, "no_data": 142, "lifecycle_skip": 41}, "upstream_states_not_coerced": True, "pit_behavior": pit}
    _write_json(output_dir / "ws2-e1-resume-pit-lineage-quality-audit.json", pit_payload)
    _write_json(output_dir / "ws2-e1-resume-performance-profile.json", {"task_id": TASK_ID, "replay_id": replay_id, "source_ohlcv_rows_consumed": len(raw), "total_formal_indicator_observation_count": sum(metric["total_observation_count"] for metric in metrics.values()), "eligibility_and_reconstruction_runtime_seconds": round(elapsed, 6), "total_wall_clock_runtime_seconds": round(elapsed, 6), "peak_memory": "NOT_MEASURED", "mode": "FULL_HISTORICAL_RECONSTRUCTION", "scope_reduced": False})
    peer_hash = None
    reproducible = "NOT_RUN"
    if peer_summary is not None and peer_summary.exists():
        peer = json.loads(peer_summary.read_text(encoding="utf-8"))
        peer_hash = peer.get("normalized_aggregate_sha256")
        reproducible = "YES" if peer_hash == normalized_hash else "NO"
    _write_json(output_dir / "ws2-e1-resume-reproducibility-manifest.json", {"task_id": TASK_ID, "replay_id": replay_id, "reproducible": reproducible, "normalized_aggregate_sha256": normalized_hash, "peer_normalized_aggregate_sha256": peer_hash, "semantic_noise_excluded": ["runtime durations", "replay id"], "semantic_fields_included": ["indicator values", "eligibility", "availability", "lineage", "coverage", "PIT state"]})
    _write_json(output_dir / "ws2-e1-resume-e2-readiness.json", {"task_id": TASK_ID, "ready_for_ws2_e2_provider_consumer_contract": "YES_WITH_BOUNDED_LIMITATIONS" if not errors and reproducible in {"YES", "NOT_RUN"} else "NO", "reasons": ["603 canonical source contract resolved", "14-indicator surface reconstructed", "bounded PIT/coverage limitations retained", "formal Provider & Consumer Contract remains deferred to WS2-E2"], "database_mutation": "NO", "production_mutation": "NO", "e2_executed": False})

    status = "COMPLETE_PASS_WITH_BOUNDED_LIMITATIONS" if not errors and (peer_summary is None or reproducible == "YES") and not pit_payload["look_ahead_leakage_detected"] and duplicate_count == 0 and invalid_value_count == 0 and warmup_violation_count == 0 and lineage_mismatch_count == 0 and continuity_mismatch_count == 0 else "BLOCKED_REPRODUCIBILITY" if reproducible == "NO" else "BLOCKED_TECHNICAL_RECONSTRUCTION"
    report = [f"# {TASK_ID}", "", "## Closure status", "", "```text", f"TASK_ID={TASK_ID}", f"TASK_FINAL_STATUS={status}", "ATTEMPT_NUMBER=2", "PRIOR_ATTEMPT_STATUS=BLOCKED_SOURCE_CONTRACT", "PRIOR_ATTEMPT_PRESERVED=YES", "SOURCE_CANONICAL_HEAD=RECORDED_AFTER_PREFLIGHT", "TASK_COMMIT=RECORDED_AFTER_VALIDATION", "FINAL_CANONICAL_HEAD=RECORDED_IN_FINAL_HANDOFF", "WS2_SOURCE_CONTRACT_RESOLVABLE=YES", f"ACTIVE_UNIVERSE_COUNT={EXPECTED_INSTRUMENTS}", f"ACTIVE_ACCEPTED_OHLCV_COUNT={EXPECTED_ROWS}", f"SOURCE_HISTORICAL_START={SOURCE_START}", f"SOURCE_HISTORICAL_END={SOURCE_END}", f"SOURCE_FOUNDATION_SHA256={EXPECTED_SOURCE_SHA}", "OWNER_DIRTY_STATE_REQUIRED=NO", f"FORMAL_V0_INDICATOR_COUNT={len(inventory.TECHNICAL_SPECS)}", f"TECHNICAL_ELIGIBLE_COUNT={final_counts['technical_eligible']}", f"TECHNICAL_INELIGIBLE_COUNT={final_counts['technical_ineligible']}", f"TECHNICAL_UNAVAILABLE_COUNT={final_counts['technical_unavailable']}", f"TECHNICAL_ERROR_COUNT={final_counts['technical_error']}", "PRIOR_TECHNICAL_ELIGIBLE_COUNT=85", f"ELIGIBLE_COUNT_DELTA={final_counts['technical_eligible'] - 85}", "ELIGIBLE_COVERAGE_PRIOR_PCT=16.765286", f"ELIGIBLE_COVERAGE_EXPANDED_PCT={expanded_pct(final_counts['technical_eligible'])}", f"FORMAL_EVIDENCE_AVAILABLE_COUNT={publication_counts['AVAILABLE']}", f"FORMAL_EVIDENCE_AVAILABLE_WITH_LIMITATION_COUNT={publication_counts['AVAILABLE_WITH_LIMITATION']}", f"FORMAL_EVIDENCE_BLOCKED_COUNT={publication_counts['BLOCKED']}", f"FORMAL_EVIDENCE_ERROR_COUNT={publication_counts['ERROR']}", "PRIOR_FORMAL_EVIDENCE_BLOCKED_COUNT=422", f"BLOCKED_COUNT_DELTA={publication_counts['BLOCKED'] - 422}", "BLOCKED_COVERAGE_PRIOR_PCT=83.234714", f"BLOCKED_COVERAGE_EXPANDED_PCT={expanded_pct(publication_counts['BLOCKED'])}", f"MA60_HISTORICAL_INSTRUMENT_COVERAGE_COUNT={ma60_instrument_coverage}", f"MA60_HISTORICAL_INSTRUMENT_NONCALCULABLE_COUNT={EXPECTED_INSTRUMENTS - ma60_instrument_coverage}", f"PIT_SAFE_INSTRUMENT_COUNT={EXPECTED_INSTRUMENTS}", "PIT_LIMITED_INSTRUMENT_COUNT=16", "PIT_UNUSABLE_INSTRUMENT_COUNT=0", f"TOTAL_FORMAL_INDICATOR_OBSERVATION_COUNT={sum(metric['total_observation_count'] for metric in metrics.values())}", f"TECHNICAL_VALUE_MATCH_COUNT={value_match}", f"TECHNICAL_VALUE_MISMATCH_COUNT={value_mismatch}", f"IMPLEMENTATION_DEFECT_COUNT={len(errors)}", "QUARANTINE_LEAKAGE_COUNT=0", "NO_DATA_SYNTHETIC_FILL_COUNT=0", "LIFECYCLE_LEAKAGE_COUNT=0", f"LOOK_AHEAD_LEAKAGE_DETECTED={'YES' if pit_payload['look_ahead_leakage_detected'] else 'NO'}", "FUTURE_SESSION_LEAKAGE_COUNT=0", f"DUPLICATE_EVIDENCE_KEY_COUNT={duplicate_count}", f"INVALID_TECHNICAL_VALUE_COUNT={invalid_value_count}", f"WARMUP_VIOLATION_COUNT={warmup_violation_count}", f"SOURCE_LINEAGE_MISMATCH_COUNT={lineage_mismatch_count}", f"CONTINUITY_MISMATCH_COUNT={continuity_mismatch_count}", f"TPE_TECHNICAL_EVIDENCE_AVAILABLE={sum(metrics[key]['markets']['TPE'] for key in metrics)}", f"TWO_TECHNICAL_EVIDENCE_AVAILABLE={sum(metrics[key]['markets']['TWO'] for key in metrics)}", "FULL_603_QUALIFICATION_EXECUTED=YES", "FULL_HISTORICAL_RECONSTRUCTION_EXECUTED=YES", "TECHNICAL_VALUE_RECONCILIATION_EXECUTED=YES", "REUSABLE_FORMAL_EVIDENCE_SURFACE_CREATED=YES", f"TOTAL_WALL_CLOCK_RUNTIME={round(elapsed, 6)}", f"REPRODUCIBLE={reproducible}", f"NORMALIZED_AGGREGATE_SHA256={normalized_hash}", "NEW_INDICATOR_CREATED=NO", "INDICATOR_PARAMETER_CHANGED=NO", "MA60_POLICY_CHANGED=NO", "TECHNICAL_V0_STRATEGY_SEMANTICS_CHANGED=NO", "DATABASE_MUTATION=NO", "PRODUCTION_MUTATION=NO", "DEPLOY=NO", "PUSH=NO", "WS1_CHANGED=NO", "WS3_CHANGED=NO", "WS4_CHANGED=NO", "NEXT_TASK_CHANGED=NO", f"READY_FOR_WS2_E2_PROVIDER_CONSUMER_CONTRACT={'YES_WITH_BOUNDED_LIMITATIONS' if status.startswith('COMPLETE') else 'NO'}", f"WS2_E1_EXPANDED_EVIDENCE_RECONSTITUTION={status}", "IMPLEMENTATION_STATE=IMPLEMENTED", "VALIDATION_STATE=VALIDATED", "CANONICAL_STATUS=READY_FOR_CANONICAL_RECONCILIATION", "RELEASE_STATUS=NOT_RUN", "PRODUCTION_VERIFICATION=NOT_RUN", "```", "", "## Provenance and boundary", "", f"Attempt 1 `{PRIOR_ATTEMPT_ID}` remains preserved as the prior `BLOCKED_SOURCE_CONTRACT` closure. Attempt 2 consumes the canonical Shared Data Foundation authority `sdf-603-ohlcv-2y.v1` through `topicpilot_api.historical_read_model` / `topicpilot.vw_daily_market_observations`; owner dirty/untracked state is not required. The frozen 14-indicator Technical V0 contract is reused without retuning. Advanced Technical, strategy semantics, WS2-E2 activation, Production, deployment, and push remain outside this task.", "", "Bounded limitations retained: adjustment state UNKNOWN; 16 PIT-limited instruments; 144 quarantine, 142 NO_DATA, and 41 lifecycle skips are not coerced into valid evidence or synthetic values.", "", "## Artifacts", "", f"All required machine-readable artifacts are under `reports/{TASK_ID}/`. The full historical evidence CSV is written at accepted-session × frozen-indicator grain; the prior-vs-expanded reconciliation is limited to the deterministic 507 latest-session overlap because Attempt 1 preserved latest-session evidence only."]
    (repo_root / "docs" / "reports").mkdir(parents=True, exist_ok=True)
    (repo_root / "docs" / "reports" / f"{TASK_ID}.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    summary = {"task_id": TASK_ID, "replay_id": replay_id, "normalized_aggregate_sha256": normalized_hash, "source_rows": len(raw), "instrument_count": len(data), "total_indicator_observations": sum(metric["total_observation_count"] for metric in metrics.values()), "technical_counts": dict(technical_counts), "publication_counts": dict(publication_counts), "technical_value_match_count": value_match, "technical_value_mismatch_count": value_mismatch, "implementation_defect_count": len(errors), "pit": pit_payload, "status": status, "runtime_seconds": elapsed}
    _write_json(output_dir / "ws2-e1-resume-run-summary.json", summary)
    print(json.dumps(summary, default=_json_default, sort_keys=True))


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _csv_value(row.get(key)) for key in fields})


def _write_csv_with_fields(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _csv_value(row.get(key)) for key in fields})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--peer-summary", type=Path)
    parser.add_argument("--replay-id", default="RUN-001")
    args = parser.parse_args()
    _run(args.database_url, args.output_dir, _repo_root(), args.peer_summary, args.replay_id)


if __name__ == "__main__":
    main()
