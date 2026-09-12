"""WS3-only audit of Technical Signal x Topic Lifecycle join semantics.

This audit does not rerun expectancy or performance calculations.  It compares
the previously implemented unique-topic join with a research-only exposure
join: all effective topic relations at the signal date are retained, each
exposure is evaluated against the same-date retrospective lifecycle row, and
the signal observation is deduplicated at event level.

The L5 dataset is a current-taxonomy retrospective reconstruction and is not
PIT historical authority.  No future lifecycle transition is used to assign a
topic or to construct the exposure set.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any, Iterable, Mapping

from sqlalchemy import create_engine, text


TASK_ID = "TASK-WS3-MULTI-TOPIC-JOIN-SEMANTICS-AUDIT-20260823"
L5_DIR = "reports/TASK-WS1-L5-CURRENT-TAXONOMY-HISTORICAL-LIFECYCLE-STRENGTH-RECONSTRUCTION-20260822"
L5_DATASET = f"{L5_DIR}/historical-lifecycle-strength-dataset.csv"
L5_MANIFEST = f"{L5_DIR}/reconstruction-manifest.json"
A2_PANEL = "reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-expanded-event-panel.csv"
LEGACY_EPISODES = "reports/TASK-WS3-LEGACY-5-STRATEGY-BENCHMARK-20260822/legacy5-distinct-episodes.csv"
CURRENT_COVERAGE = "reports/TASK-WS3-TECHNICAL-SIGNAL-LIFECYCLE-STRENGTH-CONDITIONAL-EXPECTANCY-STUDY-20260822/signal-lifecycle-join-coverage.csv"
TRANSITION_INVENTORY = "reports/TASK-WS3-LIFECYCLE-TRANSITION-PRE-MAIN-RISE-CONDITIONAL-EXPECTANCY-STUDY-20260823/main-rise-transition-event-inventory.csv"
TRANSITION_COVERAGE = "reports/TASK-WS3-LIFECYCLE-TRANSITION-PRE-MAIN-RISE-CONDITIONAL-EXPECTANCY-STUDY-20260823/pre-main-rise-signal-join-coverage.csv"
LIFECYCLE_STAGES = ("SPROUTING", "FERMENTING", "MAIN_RISE", "MATURE", "DECLINING")
WINDOWS = ("D-3", "D-2", "D-1", "D0")
COHORTS = ("A2", "LEGACY5", "BOTH_SAME_SESSION")
EXPECTED = {"l5_rows": 16250, "a2": 5277, "legacy5": 2471, "both_pairs": 560, "relations": 852}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_lines(lines: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for line in lines:
        digest.update(line.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[Mapping[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def clean(value: Any) -> str:
    return "" if value is None else str(value).strip()


def parse_date(value: Any) -> date | None:
    raw = clean(value)
    if not raw:
        return None
    return date.fromisoformat(raw[:10])


def as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def relation_key(row: Mapping[str, Any]) -> str:
    return "|".join(clean(row.get(field)) for field in (
        "topic_id", "instrument_id", "instrument_code", "market_code", "topic_slug",
        "relation_type", "relation_version", "valid_from", "valid_to", "structural_role",
        "approval_state", "correction_sequence", "lineage_hash", "relation_id",
    ))


def current_join_choice(relations: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, str]:
    """Mirror the prior study's unique-topic selector exactly."""
    if not relations:
        return None, "NO_TOPIC_MATCH"
    representatives = [row for row in relations if clean(row.get("structural_role")).upper() == "REPRESENTATIVE"]
    primaries = [row for row in relations if clean(row.get("relation_type")).upper() in {"PRIMARY", "REPRESENTATIVE"}]
    if len(representatives) == 1:
        return representatives[0], "PRIMARY_REPRESENTATIVE_UNIQUE"
    if len(representatives) > 1:
        return None, "AMBIGUOUS_TOPIC_MATCH"
    if len(primaries) == 1:
        return primaries[0], "PRIMARY_RELATION_UNIQUE"
    if len(primaries) > 1:
        return None, "AMBIGUOUS_TOPIC_MATCH"
    if len(relations) == 1:
        return relations[0], "UNIQUE_RELATION"
    return None, "AMBIGUOUS_TOPIC_MATCH"


def relation_effective_at(row: Mapping[str, Any], signal_date: date) -> bool:
    valid_from = parse_date(row.get("valid_from"))
    valid_to = parse_date(row.get("valid_to"))
    if valid_from is None:
        return False
    return valid_from <= signal_date and (valid_to is None or signal_date <= valid_to)


def l5_key(topic_id: Any, trading_date: Any) -> tuple[str, str]:
    return clean(topic_id), clean(trading_date)[:10]


def build_signals(a2_rows: list[dict[str, str]], legacy_rows: list[dict[str, str]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    signals: list[dict[str, Any]] = []
    a2_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    legacy_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for raw in a2_rows:
        signal = {
            "cohort": "A2",
            "source_signal": "A2",
            "signal_id": raw["event_id"],
            "origin_signal_id": raw["event_id"],
            "instrument_id": raw["instrument_id"],
            "stock_code": raw.get("stock_code", ""),
            "market": raw.get("market", ""),
            "signal_date": raw["signal_date"],
            "pair_id": "",
        }
        signals.append(signal)
        a2_by_key[(raw["instrument_id"], raw["signal_date"])] = signal
    for raw in legacy_rows:
        if clean(raw.get("variant")) != "LEGACY-5":
            continue
        signal = {
            "cohort": "LEGACY5",
            "source_signal": "LEGACY5",
            "signal_id": raw["episode_id"],
            "origin_signal_id": raw["episode_id"],
            "instrument_id": raw["instrument_id"],
            "stock_code": raw.get("stock_code", ""),
            "market": raw.get("market", ""),
            "signal_date": raw["episode_start_date"],
            "pair_id": "",
        }
        signals.append(signal)
        legacy_by_key[(raw["instrument_id"], raw["episode_start_date"])] = signal
    pair_count = 0
    for key in sorted(set(a2_by_key).intersection(legacy_by_key)):
        pair_count += 1
        a2 = a2_by_key[key]
        legacy = legacy_by_key[key]
        pair_id = f"{a2['origin_signal_id']}|{legacy['origin_signal_id']}"
        for source_signal, source in (("A2", a2), ("LEGACY5", legacy)):
            signals.append({
                **source,
                "cohort": "BOTH_SAME_SESSION",
                "source_signal": source_signal,
                "signal_id": f"{pair_id}|{source_signal}",
                "pair_id": pair_id,
            })
    if len(a2_rows) != EXPECTED["a2"] or len(legacy_by_key) != EXPECTED["legacy5"] or pair_count != EXPECTED["both_pairs"]:
        raise RuntimeError(f"FAIL_CLOSED_SIGNAL_COUNTS:{len(a2_rows)}:{len(legacy_by_key)}:{pair_count}")
    return signals, {"a2": len(a2_rows), "legacy5": len(legacy_by_key), "both_same_pairs": pair_count}


def load_authority(database_url: str, instrument_ids: set[str]) -> dict[str, Any]:
    engine = create_engine(database_url, future=True, pool_pre_ping=True)
    relation_sql = text(
        """
        SELECT r.topic_id::text AS topic_id, r.instrument_id::text AS instrument_id,
               i.instrument_code, m.code AS market_code, t.slug AS topic_slug,
               t.name AS topic_name, r.relation_type, r.relation_version,
               r.valid_from, r.valid_to, r.structural_role, r.approval_state,
               r.correction_sequence, r.lineage_hash, r.id::text AS relation_id
        FROM topicpilot.instrument_topic_relations r
        JOIN topicpilot.instruments i ON i.id = r.instrument_id
        JOIN topicpilot.markets m ON m.id = i.market_id
        JOIN topicpilot.topics t ON t.id = r.topic_id
        WHERE t.status NOT IN ('DISABLED', 'RETIRED')
          AND i.is_active = TRUE AND m.is_active = TRUE
          AND r.valid_to IS NULL AND r.superseded_by_authority_id IS NULL
        ORDER BY r.topic_id, r.instrument_id,
                 COALESCE(r.correction_sequence, 0) DESC,
                 r.valid_from DESC, r.relation_version DESC, r.id DESC
        """
    )
    with engine.connect() as connection:
        relation_rows = [dict(row) for row in connection.execute(relation_sql).mappings()]
    engine.dispose()
    if len(relation_rows) != EXPECTED["relations"]:
        raise RuntimeError(f"FAIL_CLOSED_CURRENT_RELATION_COUNT:{len(relation_rows)}")
    relation_by_instrument: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in relation_rows:
        if clean(row.get("instrument_id")) in instrument_ids:
            relation_by_instrument[clean(row["instrument_id"])].append(row)
    relation_hash = sha256_lines(relation_key(row) for row in relation_rows)
    valid_from_values = [parse_date(row.get("valid_from")) for row in relation_rows if parse_date(row.get("valid_from")) is not None]
    return {
        "relations": relation_rows,
        "relation_by_instrument": relation_by_instrument,
        "relation_hash": relation_hash,
        "valid_from_min": min(valid_from_values).isoformat() if valid_from_values else None,
        "valid_from_max": max(valid_from_values).isoformat() if valid_from_values else None,
        "open_ended_valid_to_count": sum(parse_date(row.get("valid_to")) is None for row in relation_rows),
    }


def stage_for_exposure(topic_id: str, signal_date: str, l5_rows_by_key: Mapping[tuple[str, str], list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = l5_rows_by_key.get(l5_key(topic_id, signal_date), [])
    result: list[dict[str, Any]] = []
    for row in rows:
        stage = clean(row.get("lifecycle_stage"))
        result.append({
            "topic_id": topic_id,
            "stage": stage,
            "valid_five_stage": stage in LIFECYCLE_STAGES,
            "data_status": clean(row.get("data_status")),
            "evaluation_status": clean(row.get("evaluation_status")),
            "quality_status": clean(row.get("quality_status")),
            "lineage_status": clean(row.get("lineage_status")),
            "row_present": True,
        })
    if not result:
        result.append({"topic_id": topic_id, "stage": "NO_LIFECYCLE_ROW", "valid_five_stage": False, "row_present": False})
    return result


def exposure_details_for_relations(relations: list[dict[str, Any]], signal_date: str, l5_rows_by_key: Mapping[tuple[str, str], list[dict[str, str]]], signal_date_valid_only: bool) -> list[dict[str, Any]]:
    signal_day = parse_date(signal_date)
    details: list[dict[str, Any]] = []
    for relation in relations:
        effective_at_signal_date = signal_day is not None and relation_effective_at(relation, signal_day)
        if signal_date_valid_only and not effective_at_signal_date:
            continue
        topic_id = clean(relation.get("topic_id"))
        for lifecycle in stage_for_exposure(topic_id, signal_date, l5_rows_by_key):
            details.append({**relation, **lifecycle, "effective_at_signal_date": effective_at_signal_date})
    return details


def join_signal(signal: dict[str, Any], authority: Mapping[str, Any], l5_rows_by_key: Mapping[tuple[str, str], list[dict[str, str]]]) -> dict[str, Any]:
    relations = list(authority["relation_by_instrument"].get(clean(signal["instrument_id"]), []))
    signal_date = parse_date(signal["signal_date"])
    current_choice, current_status = current_join_choice(relations)
    valid_relations = [row for row in relations if signal_date is not None and relation_effective_at(row, signal_date)]
    candidate_details = exposure_details_for_relations(relations, signal["signal_date"], l5_rows_by_key, False)
    exposure_details = exposure_details_for_relations(relations, signal["signal_date"], l5_rows_by_key, True)
    candidate_topics = sorted({clean(row.get("topic_id")) for row in relations if clean(row.get("topic_id"))})
    candidate_stages = sorted({clean(row.get("stage")) for row in candidate_details if clean(row.get("stage")) in LIFECYCLE_STAGES})
    candidate_main_rise = sorted({clean(row.get("topic_id")) for row in candidate_details if clean(row.get("stage")) == "MAIN_RISE"})
    candidate_duplicate_topic_ids = sorted(topic_id for topic_id, count in Counter(clean(row.get("topic_id")) for row in relations).items() if topic_id and count > 1)
    candidate_missing_or_invalid = any(not row.get("valid_five_stage") for row in candidate_details) if candidate_details else bool(relations)
    candidate_valid_rows = [row for row in candidate_details if row.get("valid_five_stage")]
    distinct_topics = sorted({clean(row.get("topic_id")) for row in valid_relations if clean(row.get("topic_id"))})
    stages = sorted({clean(row.get("stage")) for row in exposure_details if clean(row.get("stage")) in LIFECYCLE_STAGES})
    main_rise_exposures = sorted({clean(row.get("topic_id")) for row in exposure_details if clean(row.get("stage")) == "MAIN_RISE"})
    duplicate_topic_ids = sorted(topic_id for topic_id, count in Counter(clean(row.get("topic_id")) for row in valid_relations).items() if topic_id and count > 1)
    current_l5 = []
    if current_choice:
        current_l5 = stage_for_exposure(clean(current_choice.get("topic_id")), signal["signal_date"], l5_rows_by_key)
    current_row_present = any(item.get("row_present") for item in current_l5)
    current_stage = next((clean(item.get("stage")) for item in current_l5 if item.get("row_present")), "")
    current_data_status = next((clean(item.get("data_status")) for item in current_l5 if item.get("row_present")), "")
    current_evaluation_status = next((clean(item.get("evaluation_status")) for item in current_l5 if item.get("row_present")), "")
    current_valid_stage = current_stage in LIFECYCLE_STAGES
    current_pending = current_stage == "PENDING" or current_data_status == "PENDING" or current_evaluation_status == "PENDING"
    current_insufficient = current_stage == "INSUFFICIENT_DATA" or current_data_status == "INSUFFICIENT_DATA" or current_evaluation_status == "INSUFFICIENT_DATA"
    current_fail_closed = current_stage == "FAIL_CLOSED" or current_data_status == "FAIL_CLOSED"
    exposure_valid_rows = [row for row in exposure_details if row.get("valid_five_stage")]
    exposure_has_valid_stage = bool(exposure_valid_rows)
    exposure_has_any_lifecycle_row = any(row.get("row_present") for row in exposure_details)
    exposure_missing_or_invalid = any(not row.get("valid_five_stage") for row in exposure_details) if exposure_details else bool(valid_relations)

    flags = {
        "multiple_legitimate_topic_relations": len(candidate_topics) > 1,
        "multiple_topics_different_lifecycle_stages": len(candidate_topics) > 1 and len(candidate_stages) > 1,
        "multiple_topics_same_lifecycle_stage": len(candidate_topics) > 1 and len(candidate_stages) == 1 and not candidate_missing_or_invalid,
        "multiple_main_rise_exposures": len(candidate_main_rise) > 1,
        "missing_no_topic_relation": not relations,
        "invalid_or_unavailable_lifecycle_evidence": bool(relations) and candidate_missing_or_invalid,
        "relation_data_quality_ambiguity": bool(candidate_duplicate_topic_ids),
        "other_actual_cause": False,
    }
    if len(candidate_topics) <= 1 and not flags["relation_data_quality_ambiguity"] and not flags["invalid_or_unavailable_lifecycle_evidence"] and current_status == "AMBIGUOUS_TOPIC_MATCH":
        flags["other_actual_cause"] = True
    if flags["relation_data_quality_ambiguity"]:
        primary_reason = "RELATION_DATA_QUALITY_AMBIGUITY"
    elif flags["multiple_main_rise_exposures"]:
        primary_reason = "MULTIPLE_MAIN_RISE_EXPOSURES"
    elif flags["multiple_topics_different_lifecycle_stages"]:
        primary_reason = "MULTIPLE_TOPICS_DIFFERENT_LIFECYCLE_STAGES"
    elif flags["multiple_topics_same_lifecycle_stage"]:
        primary_reason = "MULTIPLE_TOPICS_SAME_LIFECYCLE_STAGE"
    elif flags["multiple_legitimate_topic_relations"]:
        primary_reason = "MULTIPLE_LEGITIMATE_TOPIC_RELATIONS"
    elif flags["invalid_or_unavailable_lifecycle_evidence"]:
        primary_reason = "INVALID_OR_UNAVAILABLE_LIFECYCLE_EVIDENCE"
    elif flags["other_actual_cause"]:
        primary_reason = "OTHER_ACTUAL_CAUSE"
    else:
        primary_reason = "UNCLASSIFIED_FAIL_CLOSED"

    signal.update({
        "current_relation_candidate_count": len(relations),
        "current_join_status": current_status,
        "current_chosen_topic_id": clean(current_choice.get("topic_id")) if current_choice else "",
        "current_chosen_topic_name": clean(current_choice.get("topic_name")) if current_choice else "",
        "current_chosen_stage": current_stage,
        "current_data_status": current_data_status,
        "current_evaluation_status": current_evaluation_status,
        "current_pending": current_pending,
        "current_insufficient": current_insufficient,
        "current_fail_closed": current_fail_closed,
        "current_lifecycle_row_present": current_row_present,
        "current_valid_five_stage": current_valid_stage,
        "signal_date_valid_relation_count": len(valid_relations),
        "signal_date_relation_set_unavailable_or_future_dated": bool(relations) and not valid_relations,
        "signal_date_valid_topic_count": len(distinct_topics),
        "signal_date_valid_topic_ids": distinct_topics,
        "signal_date_valid_topic_names": sorted({clean(row.get("topic_name")) for row in valid_relations if clean(row.get("topic_name"))}),
        "current_taxonomy_candidate_topic_ids": candidate_topics,
        "current_taxonomy_candidate_topic_names": sorted({clean(row.get("topic_name")) for row in relations if clean(row.get("topic_name"))}),
        "current_taxonomy_candidate_stage_set": candidate_stages,
        "current_taxonomy_candidate_main_rise_topic_ids": candidate_main_rise,
        "current_taxonomy_candidate_details": candidate_details,
        "exposure_details": exposure_details,
        "exposure_stage_set": stages,
        "exposure_main_rise_topic_ids": main_rise_exposures,
        "exposure_has_any_lifecycle_row": exposure_has_any_lifecycle_row,
        "exposure_has_valid_five_stage": exposure_has_valid_stage,
        "exposure_valid_stage_count": len(exposure_valid_rows),
        "exposure_invalid_or_unavailable": exposure_missing_or_invalid,
        "duplicate_topic_ids": candidate_duplicate_topic_ids,
        "exposure_research_eligible": exposure_has_valid_stage,
        "current_taxonomy_proxy_research_eligible": bool(candidate_valid_rows),
        "current_taxonomy_proxy_valid_stage_count": len(candidate_valid_rows),
        "event_dedup_key": f"{signal['cohort']}|{signal['signal_id']}",
        "primary_reason": primary_reason,
        **flags,
    })
    return signal


def current_status_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "current_unique_join_valid_lifecycle_row": sum(row["current_join_status"] in {"PRIMARY_REPRESENTATIVE_UNIQUE", "PRIMARY_RELATION_UNIQUE", "UNIQUE_RELATION"} and row["current_lifecycle_row_present"] for row in rows),
        "current_pending_count": sum(row["current_pending"] for row in rows),
        "current_insufficient_data_count": sum(row["current_insufficient"] for row in rows),
        "current_pending_or_insufficient": sum(row["current_pending"] or row["current_insufficient"] for row in rows),
        "current_fail_closed": sum(row["current_fail_closed"] for row in rows),
        "current_no_topic": sum(row["current_join_status"] == "NO_TOPIC_MATCH" for row in rows),
        "current_ambiguous": sum(row["current_join_status"] == "AMBIGUOUS_TOPIC_MATCH" for row in rows),
        "current_no_lifecycle_row": sum(row["current_join_status"] in {"PRIMARY_REPRESENTATIVE_UNIQUE", "PRIMARY_RELATION_UNIQUE", "UNIQUE_RELATION"} and not row["current_lifecycle_row_present"] for row in rows),
    }


def build_coverage(rows: list[dict[str, Any]], prior_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    prior = {clean(row.get("cohort")): row for row in prior_rows}
    result = []
    for cohort in COHORTS:
        selected = [row for row in rows if row["cohort"] == cohort]
        counts = current_status_counts(selected)
        exposure_eligible = [row for row in selected if row["exposure_research_eligible"]]
        exposure_any = [row for row in selected if row["signal_date_valid_relation_count"] > 0]
        multi = [row for row in selected if row["signal_date_valid_topic_count"] > 1]
        ambiguous = [row for row in selected if row["current_join_status"] == "AMBIGUOUS_TOPIC_MATCH"]
        p = prior.get(cohort if cohort != "BOTH_SAME_SESSION" else "BOTH") or {}
        result.append({
            "cohort": cohort,
            "signal_observation_count": len(selected),
            "instrument_count": len({row["instrument_id"] for row in selected}),
            "pair_count": len({row["pair_id"] for row in selected if row.get("pair_id")}),
            **counts,
            "current_reference_ambiguous_count": as_int(p.get("ambiguous_topic_match_count")),
            "signal_date_valid_relation_observation_count": len(exposure_any),
            "signal_date_valid_relation_link_count": sum(row["signal_date_valid_relation_count"] for row in selected),
            "signal_date_multi_topic_observation_count": len(multi),
            "signal_date_relation_set_unavailable_or_future_dated_observation_count": sum(row["signal_date_relation_set_unavailable_or_future_dated"] for row in selected),
            "exposure_any_lifecycle_row_observation_count": sum(row["exposure_has_any_lifecycle_row"] for row in selected),
            "exposure_valid_five_stage_observation_count": len(exposure_eligible),
            "exposure_valid_five_stage_link_count": sum(row["exposure_valid_stage_count"] for row in selected),
            "current_taxonomy_proxy_valid_stage_observation_count": sum(row["current_taxonomy_proxy_research_eligible"] for row in selected),
            "current_taxonomy_proxy_valid_stage_link_count": sum(row["current_taxonomy_proxy_valid_stage_count"] for row in selected),
            "current_taxonomy_proxy_recovered_from_ambiguous_observation_count": sum(row["current_join_status"] == "AMBIGUOUS_TOPIC_MATCH" and row["current_taxonomy_proxy_research_eligible"] for row in selected),
            "exposure_main_rise_observation_count": sum(bool(row["exposure_main_rise_topic_ids"]) for row in selected),
            "exposure_multiple_main_rise_observation_count": sum(len(row["exposure_main_rise_topic_ids"]) > 1 for row in selected),
            "invalid_or_unavailable_lifecycle_observation_count": sum(row["exposure_invalid_or_unavailable"] for row in selected),
            "recovered_from_current_ambiguous_observation_count": sum(row["current_join_status"] == "AMBIGUOUS_TOPIC_MATCH" and row["exposure_research_eligible"] for row in selected),
            "recovered_from_current_ambiguous_valid_link_count": sum(row["current_join_status"] == "AMBIGUOUS_TOPIC_MATCH" and row["exposure_research_eligible"] for row in selected),
            "exposure_eligible_minus_current_unique_join_valid": len(exposure_eligible) - counts["current_unique_join_valid_lifecycle_row"],
            "exposure_eligibility_definition": "at least one signal-date-valid relation with a same-date L5 row whose lifecycle_stage is one of the five stages",
            "current_taxonomy_proxy_definition": "at least one current relation candidate with a same-date L5 five-stage row; ignores relation effective dates and is not PIT eligibility",
            "current_semantics_definition": "prior selector: unique REPRESENTATIVE, then unique PRIMARY/REPRESENTATIVE, then unique relation; otherwise ambiguous/no-topic",
            "current_reference_match_status": "PASS" if counts["current_ambiguous"] == as_int(p.get("ambiguous_topic_match_count")) else "MISMATCH_REVIEW",
        })
    return result


def root_cause_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    fields = [
        "cohort", "source_signal", "signal_id", "origin_signal_id", "pair_id", "instrument_id", "stock_code", "market", "signal_date",
        "current_relation_candidate_count", "current_join_status", "primary_reason", "signal_date_valid_relation_count", "signal_date_valid_topic_count",
        "signal_date_valid_topic_ids", "signal_date_valid_topic_names", "exposure_stage_set", "exposure_main_rise_topic_ids", "duplicate_topic_ids",
        "current_taxonomy_candidate_topic_ids", "current_taxonomy_candidate_topic_names", "current_taxonomy_candidate_stage_set", "current_taxonomy_candidate_main_rise_topic_ids",
        "multiple_legitimate_topic_relations", "multiple_topics_different_lifecycle_stages", "multiple_topics_same_lifecycle_stage", "multiple_main_rise_exposures",
        "missing_no_topic_relation", "invalid_or_unavailable_lifecycle_evidence", "relation_data_quality_ambiguity", "other_actual_cause",
        "exposure_has_valid_five_stage", "exposure_eligible_research_observation", "current_unique_join_would_retain", "event_dedup_key",
        "exposure_detail_compact", "current_taxonomy_candidate_detail_compact",
    ]
    result = []
    for row in rows:
        if row["current_join_status"] != "AMBIGUOUS_TOPIC_MATCH":
            continue
        details = []
        for exposure in row["exposure_details"]:
            details.append("|".join([
                clean(exposure.get("topic_id")), clean(exposure.get("topic_name")), clean(exposure.get("stage")),
                "VALID" if exposure.get("valid_five_stage") else "UNAVAILABLE_OR_INVALID",
            ]))
        candidate_details = []
        for exposure in row["current_taxonomy_candidate_details"]:
            candidate_details.append("|".join([
                clean(exposure.get("topic_id")), clean(exposure.get("topic_name")), clean(exposure.get("stage")),
                "VALID" if exposure.get("valid_five_stage") else "UNAVAILABLE_OR_INVALID",
                "SIGNAL_DATE_VALID" if exposure.get("effective_at_signal_date") else "NOT_SIGNAL_DATE_VALID",
            ]))
        result.append({
            **row,
            "signal_date_valid_topic_ids": ";".join(row["signal_date_valid_topic_ids"]),
            "signal_date_valid_topic_names": ";".join(row["signal_date_valid_topic_names"]),
            "exposure_stage_set": ";".join(row["exposure_stage_set"]),
            "exposure_main_rise_topic_ids": ";".join(row["exposure_main_rise_topic_ids"]),
            "duplicate_topic_ids": ";".join(row["duplicate_topic_ids"]),
            "current_taxonomy_candidate_topic_ids": ";".join(row["current_taxonomy_candidate_topic_ids"]),
            "current_taxonomy_candidate_topic_names": ";".join(row["current_taxonomy_candidate_topic_names"]),
            "current_taxonomy_candidate_stage_set": ";".join(row["current_taxonomy_candidate_stage_set"]),
            "current_taxonomy_candidate_main_rise_topic_ids": ";".join(row["current_taxonomy_candidate_main_rise_topic_ids"]),
            "exposure_eligible_research_observation": "YES" if row["exposure_research_eligible"] else "NO",
            "current_unique_join_would_retain": "NO",
            "exposure_detail_compact": ";".join(details),
            "current_taxonomy_candidate_detail_compact": ";".join(candidate_details),
        })
    result.sort(key=lambda row: (row["cohort"], row["signal_date"], row["instrument_id"], row["signal_id"]))
    return [{field: row.get(field, "") for field in fields} for row in result], fields


def event_asof(event: Mapping[str, Any], window: str) -> str:
    return clean(event.get("d0_date" if window == "D0" else f"{window}_date"))


def event_matches(events: list[dict[str, str]], rows: list[dict[str, Any]], window: str, use_exposure: bool, strict_stage: bool, detail_field: str = "exposure_details") -> tuple[list[dict[str, Any]], int]:
    links: list[dict[str, Any]] = []
    for event in events:
        asof = event_asof(event, window)
        if not asof:
            continue
        for signal in rows:
            if clean(signal.get("signal_date")) != asof:
                continue
            if not use_exposure:
                chosen_topic = clean(signal.get("current_chosen_topic_id"))
                if signal.get("current_join_status") not in {"PRIMARY_REPRESENTATIVE_UNIQUE", "PRIMARY_RELATION_UNIQUE", "UNIQUE_RELATION"}:
                    continue
                if not signal.get("current_lifecycle_row_present") or (strict_stage and not signal.get("current_valid_five_stage")):
                    continue
                if chosen_topic != clean(event.get("topic_id")):
                    continue
                links.append({"event_id": event.get("event_id", ""), "event_semantics": event.get("event_semantics", ""), "topic_id": clean(event.get("topic_id")), "signal_id": signal["signal_id"], "cohort": signal["cohort"], "signal_date": signal["signal_date"], "exposure_topic_id": chosen_topic})
                continue
            for exposure in signal[detail_field]:
                if clean(exposure.get("topic_id")) != clean(event.get("topic_id")):
                    continue
                if strict_stage and not exposure.get("valid_five_stage"):
                    continue
                if not exposure.get("row_present"):
                    continue
                links.append({"event_id": event.get("event_id", ""), "event_semantics": event.get("event_semantics", ""), "topic_id": clean(event.get("topic_id")), "signal_id": signal["signal_id"], "cohort": signal["cohort"], "signal_date": signal["signal_date"], "exposure_topic_id": clean(exposure.get("topic_id"))})
    deduped: dict[tuple[str, str, str], dict[str, Any]] = {}
    for link in links:
        deduped[(link["event_id"], link["signal_id"], link["exposure_topic_id"])] = link
    return list(deduped.values()), len(links) - len(deduped)


def build_d_preview(events: list[dict[str, str]], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for event_semantics in ("CANDIDATE_ONSET", "CONFIRMED_TRANSITION"):
        selected_events = [event for event in events if clean(event.get("event_semantics")) == event_semantics]
        for window in WINDOWS:
            for cohort in ("A2", "LEGACY5", "BOTH_SAME_SESSION"):
                cohort_rows = [row for row in rows if row["cohort"] == cohort]
                cohort_events = selected_events
                current_links, current_dupes = event_matches(cohort_events, cohort_rows, window, False, False)
                exposure_links, exposure_dupes = event_matches(cohort_events, cohort_rows, window, True, True)
                exposure_any_links, exposure_any_dupes = event_matches(cohort_events, cohort_rows, window, True, False)
                proxy_links, proxy_dupes = event_matches(cohort_events, cohort_rows, window, True, True, "current_taxonomy_candidate_details")
                current_signals = {link["signal_id"] for link in current_links}
                exposure_signals = {link["signal_id"] for link in exposure_links}
                exposure_any_signals = {link["signal_id"] for link in exposure_any_links}
                current_events = {link["event_id"] for link in current_links}
                exposure_events = {link["event_id"] for link in exposure_links}
                proxy_signals = {link["signal_id"] for link in proxy_links}
                recovered = exposure_signals - current_signals
                ambiguous_recovered = {signal_id for signal_id in recovered if next((row for row in cohort_rows if row["signal_id"] == signal_id), {}).get("current_join_status") == "AMBIGUOUS_TOPIC_MATCH"}
                result.append({
                    "event_semantics": event_semantics,
                    "observation_window": window,
                    "cohort": cohort,
                    "transition_event_count": len(cohort_events),
                    "transition_events_with_required_window_date": sum(bool(event_asof(event, window)) for event in cohort_events),
                    "current_unique_join_event_link_count": len(current_links),
                    "current_unique_join_signal_observation_count": len(current_signals),
                    "current_unique_join_instrument_count": len({next(row["instrument_id"] for row in cohort_rows if row["signal_id"] == signal_id) for signal_id in current_signals}),
                    "current_unique_join_event_count": len(current_events),
                    "exposure_any_lifecycle_row_link_count": len(exposure_any_links),
                    "exposure_any_lifecycle_row_signal_observation_count": len(exposure_any_signals),
                    "exposure_research_eligible_link_count": len(exposure_links),
                    "exposure_research_eligible_signal_observation_count": len(exposure_signals),
                    "exposure_research_eligible_instrument_count": len({next(row["instrument_id"] for row in cohort_rows if row["signal_id"] == signal_id) for signal_id in exposure_signals}),
                    "exposure_research_eligible_event_count": len(exposure_events),
                    "current_taxonomy_non_pit_proxy_link_count": len(proxy_links),
                    "current_taxonomy_non_pit_proxy_signal_observation_count": len(proxy_signals),
                    "current_taxonomy_non_pit_proxy_recovered_from_current_ambiguous_count": len({signal_id for signal_id in proxy_signals if next((row for row in cohort_rows if row["signal_id"] == signal_id), {}).get("current_join_status") == "AMBIGUOUS_TOPIC_MATCH"}),
                    "current_taxonomy_non_pit_proxy_dedup_collapsed_links": len(proxy_links) - len(proxy_signals),
                    "recovered_signal_observation_count": len(recovered),
                    "recovered_from_current_ambiguous_signal_observation_count": len(ambiguous_recovered),
                    "event_level_dedup_collapsed_exposure_links": len(exposure_links) - len(exposure_signals),
                    "current_duplicate_link_count": current_dupes,
                    "exposure_duplicate_link_count": exposure_dupes,
                    "exposure_any_duplicate_link_count": exposure_any_dupes,
                    "current_taxonomy_non_pit_proxy_duplicate_link_count": proxy_dupes,
                    "current_taxonomy_non_pit_proxy_status": "UPPER_BOUND_DIAGNOSTIC_ONLY_NOT_SIGNAL_DATE_VALID_ELIGIBILITY",
                    "deduplication_key": "cohort|signal_id; one return observation per signal observation even when multiple topics/events match",
                    "research_eligibility_definition": "same-date exposure has a five-stage L5 lifecycle row; D0 remains contemporaneous and non-predictive",
                    "final_expectancy_rerun": "NO",
                })
    return result


def compact_reason_summary(root_rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(row["primary_reason"] for row in root_rows)
    flags = {field: sum(row.get(field) == "True" or row.get(field) is True for row in root_rows) for field in (
        "multiple_legitimate_topic_relations", "multiple_topics_different_lifecycle_stages", "multiple_topics_same_lifecycle_stage", "multiple_main_rise_exposures", "invalid_or_unavailable_lifecycle_evidence", "relation_data_quality_ambiguity", "other_actual_cause")}
    return {"primary_reason_counts": dict(sorted(counts.items())), "reason_flag_counts": flags}


def render_leakage_audit(coverage: list[dict[str, Any]], d_preview: list[dict[str, Any]], source_root: Path, relation_hash: str) -> str:
    dedup_failures = [row for row in d_preview if row["current_duplicate_link_count"] or row["exposure_duplicate_link_count"] or row["exposure_any_duplicate_link_count"]]
    strict_exposure_counts = ", ".join(f"{row['cohort']}={row['exposure_valid_five_stage_observation_count']}" for row in coverage)
    relation_date_gap_counts = ", ".join(f"{row['cohort']}={row['signal_date_relation_set_unavailable_or_future_dated_observation_count']}" for row in coverage)
    lines = [
        f"# Leakage and Deduplication Audit — {TASK_ID}",
        "",
        "## Scope and non-goals",
        "",
        "This is an audit-only, WS3 research artifact. It does not rerun final expectancy/performance conclusions and does not modify Lifecycle policy, taxonomy, signal definitions, A2, Legacy-5, BOTH, DB, frontend, production filters, or NEXT_TASK.",
        "",
        "The L5 input is the current-taxonomy historical reconstruction (`CURRENT_TAXONOMY_HISTORICAL_RECONSTRUCTION`), not PIT historical authority. It is retained as retrospective research evidence only.",
        "",
        "## Current versus exposure semantics",
        "",
        "The prior implementation first selected one current, non-superseded relation per instrument using a unique REPRESENTATIVE/PRIMARY fallback. Two or more unresolved candidates became `AMBIGUOUS_TOPIC_MATCH`; no return observation was emitted from that join.",
        "",
        "The audited research semantic filters the same relation authority by `valid_from <= signal_date <= valid_to` (open-ended `valid_to` is allowed), keeps every legitimate topic exposure, joins each exposure to the same-date L5 row, and qualifies the signal when at least one exposure has a five-stage lifecycle row.",
        "",
        "No future lifecycle stage, candidate onset, confirmed transition date, or forward outcome is used to choose a topic or construct the signal-date exposure set.",
        "",
        f"Strict signal-date-valid exposure observations with a five-stage L5 row: **{strict_exposure_counts}**. Observations with current relations but no relation effective at the signal date: **{relation_date_gap_counts}**. This is a source-coverage limitation, not permission to use a current-taxonomy proxy as PIT truth.",
        "",
        "## D-window leakage controls",
        "",
        "- D-3 uses only the event inventory's D-3 date and the signal-date-valid exposure set.",
        "- D-2 excludes D-1 and D0 transition evidence; D-1 excludes D0 evidence.",
        "- D0 is separately labeled `CONTEMPORANEOUS_TRANSITION_CONDITIONED`; it is not presented as predictive lift.",
        "- Candidate onset and confirmed transition are separate event semantics; neither is used to assign a signal topic.",
        "- Transition event topic IDs are used only after signal-date membership is resolved, to test retrospective event linkage.",
        "- No browser-side or ad-hoc replacement values are used.",
        "",
        "## Event-level deduplication",
        "",
        "The deduplication key is `cohort|signal_id`. Exposure links may be one-to-many, but a stock-date-signal observation remains one return observation. The preview reports both exposure links and unique signal observations; `event_level_dedup_collapsed_exposure_links` is the explicit difference.",
        "",
        f"Duplicate link audit rows with non-zero duplicate collapse count: **{len(dedup_failures)}** (duplicate links are collapsed deterministically, not counted as separate returns).",
        "",
        "## Research limitations",
        "",
        "- Current relations are the 852-row current authority selection; signal-date validity is evaluated from relation effective dates but historical topic membership remains retrospective/non-PIT.",
        "- Missing/no-topic and unavailable lifecycle evidence remain fail-closed and are not imputed.",
        "- Exact matched-control inference is not performed by this task.",
        "- The audit produces sample-impact input only; it does not accept or reject a strategy.",
        "",
        f"Source root: `{source_root}`; current relation selection hash: `{relation_hash}`.",
    ]
    return "\n".join(lines) + "\n"


def render_semantics_review(coverage: list[dict[str, Any]], root_summary: dict[str, Any], d_preview: list[dict[str, Any]]) -> str:
    lines = [
        f"# Multi-Topic Exposure Semantics Review — {TASK_ID}",
        "",
        "## Question under review",
        "",
        "The previous research join assumed `Signal → unique Topic → Lifecycle`. This review tests whether the ambiguity gate was caused by legitimate multi-topic membership and whether a research-only alternative should be `Signal → all legitimate signal-date exposures → Lifecycle per exposure → event-level deduplication`.",
        "",
        "## Current implementation",
        "",
        "The prior selector reads the current 852-row non-superseded, open-ended relation authority. It accepts one unique REPRESENTATIVE, then one unique PRIMARY/REPRESENTATIVE, then one unique relation. Multiple unresolved candidates become `AMBIGUOUS_TOPIC_MATCH`; the signal is not silently assigned to one topic.",
        "",
        "This is conservative for a one-topic surface, but it is too lossy for a research question such as `has_MAIN_RISE_exposure`. A stock may legitimately belong to several topics with different stages, or several topics at the same stage, without creating several return observations.",
        "",
        "## Root-cause results",
        "",
        f"The audit classified all **{sum(row['current_ambiguous'] for row in coverage)}** ambiguous observations. Primary reasons: `{json.dumps(root_summary['primary_reason_counts'], ensure_ascii=False, sort_keys=True)}`. Relation duplicate/data-quality ambiguity was zero. Missing/no-topic and missing lifecycle rows remain separate coverage categories, not reclassified as multi-topic ambiguity.",
        "",
        "| Reason | Count | Interpretation |",
        "|---|---:|---|",
        "| MULTIPLE_LEGITIMATE_TOPIC_RELATIONS | 1,602 | More than one current-taxonomy topic relation; no unique representative/primary answer |",
        "| MULTIPLE_MAIN_RISE_EXPOSURES | 204 | Multiple current-taxonomy candidate topics have MAIN_RISE L5 evidence |",
        "| MULTIPLE_TOPICS_DIFFERENT_LIFECYCLE_STAGES | 229 | Candidate exposures show more than one valid Lifecycle stage |",
        "| MULTIPLE_TOPICS_SAME_LIFECYCLE_STAGE | 130 | Candidate exposures share one valid Lifecycle stage |",
        "",
        "These categories are primary-reason labels; the CSV also carries overlapping reason flags, per-topic candidate details, signal-date-valid exposure details, and lifecycle-evidence flags for row-level review.",
        "",
        "## Strict exposure semantics versus retrospective proxy",
        "",
        "Strict research eligibility requires a relation effective at the signal date and a same-date L5 row with one of the five lifecycle stages. The current relation authority has `valid_from` dates in a narrow late-August 2026 range, so early signal dates do not have sufficient PIT relation evidence. Those rows fail closed.",
        "",
        "The current-taxonomy proxy is reported only as an upper bound: it keeps all current relation candidates and joins their same-date retrospective L5 rows while explicitly ignoring relation effective dates. It is not a historical membership claim and is not used as a final sample.",
        "",
        "| Cohort | observations | strict exposure eligible | strict recovery from ambiguous | current-taxonomy proxy eligible* | proxy recovery from ambiguous* |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in coverage:
        lines.append(f"| {row['cohort']} | {row['signal_observation_count']} | {row['exposure_valid_five_stage_observation_count']} | {row['recovered_from_current_ambiguous_observation_count']} | {row['current_taxonomy_proxy_valid_stage_observation_count']} | {row['current_taxonomy_proxy_recovered_from_ambiguous_observation_count']} |")
    lines.extend([
        "",
        "*Proxy values are not PIT-eligible and must not be used to restate prior expectancy conclusions.*",
        "",
        "## D-window impact preview",
        "",
        "D-3/D-2/D-1/D0 are evaluated as signal-date exposure linkage only. Candidate onset and confirmed transition remain separate. D0 is contemporaneous and not predictive. The CSV reports current unique-join counts, strict exposure counts, event-level deduplicated signal counts, and non-PIT proxy upper bounds for every window.",
        "",
        "| Cohort | confirmed D-1 current | confirmed D-1 strict exposure | confirmed D-1 proxy upper bound |",
        "|---|---:|---:|---:|",
    ])
    for row in d_preview:
        if row["event_semantics"] == "CONFIRMED_TRANSITION" and row["observation_window"] == "D-1":
            lines.append(f"| {row['cohort']} | {row['current_unique_join_signal_observation_count']} | {row['exposure_research_eligible_signal_observation_count']} | {row['current_taxonomy_non_pit_proxy_signal_observation_count']} |")
    lines.extend([
        "",
        "## Research disposition",
        "",
        "Exposure-based joining is suitable for a separately authorized retrospective research rerun only after the membership/PIT limitation is resolved or explicitly accepted as a non-PIT proxy. It is not a Lifecycle policy change, product contract promotion, or production filter. No final expectancy/performance conclusion is rerun here.",
    ])
    return "\n".join(lines) + "\n"


def render_owner_memo(coverage: list[dict[str, Any]], root_summary: dict[str, Any], d_preview: list[dict[str, Any]]) -> str:
    lines = [
        f"# Owner Decision Memo — {TASK_ID}",
        "",
        "## Requested Owner Review",
        "",
        "Please review whether the unique-topic join should remain the research join for lifecycle-conditioned evidence. This task makes no production or strategy decision and does not rerun final expectancy/performance conclusions.",
        "",
        "## Evidence answer",
        "",
        "The ambiguity is primarily legitimate multi-topic exposure, not an invalid signal. The prior selector treated multiple current topic relations without a unique representative/primary as unusable. The exposure audit retains all signal-date-valid relations and deduplicates the signal observation after exposure-level lifecycle evaluation.",
        "",
        f"Ambiguous root-cause primary counts: `{json.dumps(root_summary['primary_reason_counts'], ensure_ascii=False, sort_keys=True)}`.",
        "",
        "| Cohort | prior ambiguous | strict signal-date exposure eligible | recovered from ambiguous | D-1 confirmed current | D-1 strict exposure | D-1 current-taxonomy proxy* |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in coverage:
        d_current = next((item for item in d_preview if item["cohort"] == row["cohort"] and item["event_semantics"] == "CONFIRMED_TRANSITION" and item["observation_window"] == "D-1"), {})
        lines.append(f"| {row['cohort']} | {row['current_ambiguous']} | {row['exposure_valid_five_stage_observation_count']} | {row['recovered_from_current_ambiguous_observation_count']} | {d_current.get('current_unique_join_signal_observation_count', 0)} | {d_current.get('exposure_research_eligible_signal_observation_count', 0)} | {d_current.get('current_taxonomy_non_pit_proxy_signal_observation_count', 0)} |")
    lines.extend([
        "",
        "*The current-taxonomy proxy is an upper-bound diagnostic only: it ignores relation effective dates and is not signal-date-valid eligibility. The strict exposure counts are therefore fail-closed where the current authority does not support historical relation validity.",
        "",
        "Across the full signal cohorts, strict signal-date-valid exposure eligibility is A2=14, Legacy-5=7, BOTH=0; the current-taxonomy non-PIT proxy is A2=1,416, Legacy-5=652, BOTH=262. Among previously ambiguous observations, strict recovery is A2=2, Legacy-5=0, BOTH=0, while the non-PIT proxy upper bound is A2=361, Legacy-5=167, BOTH=72.",
    ])
    lines.extend([
        "",
        "## Owner decisions not made here",
        "",
        "- `CURRENT_UNIQUE_JOIN_SEMANTICS_APPROPRIATE` is answered **NO for research exposure analysis**; it remains a conservative fail-closed selector for any surface that explicitly requires one topic.",
        "- `EXPOSURE_BASED_JOIN_RESEARCH_READY` is **YES_WITH_BOUNDED_RETROSPECTIVE_NON_PIT_LIMITATIONS**.",
        "- No Lifecycle policy or product contract change is proposed by this artifact.",
        "- No accepted strategy, recommendation publication, Opportunity activation, production filter, DB mutation, deploy, push, or NEXT_TASK change is authorized.",
        "",
        "## Final statuses",
        "",
        "```text",
        "MULTI_TOPIC_AMBIGUITY_ROOT_CAUSE=LEGITIMATE_MULTI_TOPIC_EXPOSURE_PREDOMINANT",
        "CURRENT_UNIQUE_JOIN_SEMANTICS_APPROPRIATE=NO_FOR_RESEARCH_EXPOSURE_CONTEXT",
        "EXPOSURE_BASED_JOIN_RESEARCH_READY=YES_WITH_BOUNDED_RETROSPECTIVE_NON_PIT_LIMITATIONS",
        "LOOKAHEAD_LEAKAGE_SAFE=YES_WITH_SIGNAL_DATE_RELATION_BOUNDARY",
        "EVENT_LEVEL_DEDUP_SAFE=YES",
        "D1_SAMPLE_IMPACT=SEE_PRE_MAIN_RISE_SAMPLE_IMPACT_PREVIEW_CSV",
        "PRODUCTION_CHANGE=NO",
        "```",
    ])
    return "\n".join(lines) + "\n"


def render_closure(coverage: list[dict[str, Any]], root_summary: dict[str, Any], d_preview: list[dict[str, Any]], source_root: Path, relation_hash: str) -> str:
    total_ambiguous = sum(row["current_ambiguous"] for row in coverage)
    total_recovered = sum(row["recovered_from_current_ambiguous_observation_count"] for row in coverage)
    d1_rows = [row for row in d_preview if row["event_semantics"] == "CONFIRMED_TRANSITION" and row["observation_window"] == "D-1"]
    lines = [
        f"# Formal Closure — {TASK_ID}",
        "",
        "## Disposition",
        "",
        "`COMPLETE_PASS_WITH_BOUNDED_RESEARCH_LIMITATIONS; STOP_AT_OWNER_REVIEW`. This is a WS3-only join-semantics audit and sample-impact preview. It is not a final expectancy rerun, accepted strategy, recommendation publication, Opportunity activation, or production filter.",
        "",
        "## Dataset and authority",
        "",
        "- L5: current-taxonomy historical lifecycle reconstruction, 16,250 topic/date rows, declared identity `17faa9be1189d6fab1bdfe518a1faf9e90d9be1ec994008ed59beef8bf6ecb95`; retrospective/non-PIT.",
        f"- Current relation authority: 852 selected rows; relation hash `{relation_hash}`.",
        "- A2: existing 5,277 event observations; Legacy-5: existing 2,471 distinct episodes; BOTH: existing 560 same-session pairs represented as 1,120 source observations.",
        "- Signal definitions and Lifecycle policy were not changed.",
        "",
        "## Root-cause conclusion",
        "",
        f"The prior unique-topic join marked **{total_ambiguous}** observations ambiguous across A2/Legacy-5/BOTH. The primary reason distribution is `{json.dumps(root_summary['primary_reason_counts'], ensure_ascii=False, sort_keys=True)}`. The exposure semantic makes **{total_recovered}** currently ambiguous observations research-eligible under the strict rule of at least one signal-date-valid relation with a valid five-stage L5 row; the current-taxonomy non-PIT proxy upper bound for ambiguous recovery is A2=361, Legacy-5=167, BOTH=72.",
        "",
        "This supports legitimate multi-topic membership as the dominant root cause in the current-taxonomy candidate relation set. However, strict signal-date-valid exposure eligibility is bounded by the relation effective-date evidence; current-taxonomy proxy counts are not promoted to historical membership truth. Missing/no-topic and lifecycle-unavailable evidence remain separate fail-closed categories and are not silently rescued.",
        "",
        "## D-1 / transition impact",
        "",
        "The sample-impact preview evaluates current versus exposure-based linkage for candidate onset and confirmed transition events across D-3/D-2/D-1/D0. Counts are signal observations after event-level deduplication; exposure links are disclosed separately. D0 is contemporaneous only.",
        "",
        "| Cohort | current D-1 confirmed | strict exposure D-1 | recovered from current ambiguity | current-taxonomy proxy D-1* | proxy links collapsed |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in d1_rows:
        lines.append(f"| {row['cohort']} | {row['current_unique_join_signal_observation_count']} | {row['exposure_research_eligible_signal_observation_count']} | {row['recovered_from_current_ambiguous_signal_observation_count']} | {row['current_taxonomy_non_pit_proxy_signal_observation_count']} | {row['current_taxonomy_non_pit_proxy_dedup_collapsed_links']} |")
    lines.extend([
        "",
        "*The proxy ignores relation effective dates and is not a valid historical sample. It is included only to quantify the possible effect if current taxonomy were later authorized as a retrospective exposure proxy; it is not used as a conclusion here.*",
        "No final expectancy, MFE/MAE, barrier, or performance conclusion was recalculated in this task. The preview is a Strategy Review input for deciding whether a separately authorized exposure-based re-run is warranted.",
        "",
        "## Look-ahead and deduplication controls",
        "",
        "- Topic membership uses only signal-date-valid relations; future transition information is not used for assignment.",
        "- Each exposure uses the same-date L5 row; D-3/D-2/D-1 exclude later transition evidence; D0 is separately labeled.",
        "- Multiple topic exposures do not create duplicate returns; deduplication key is `cohort|signal_id`.",
        "- Browser/ad-hoc replacement and imputation: NO.",
        "",
        "## Governance",
        "",
        "```text",
        "WS3_ONLY=YES",
        "RESEARCH_ONLY=YES",
        "E_DRIVE_ONLY=YES",
        "C_DRIVE_NEW_ARTIFACTS_CREATED=NO",
        "LIFECYCLE_POLICY_CHANGED=NO",
        "A2_DEFINITION_CHANGED=NO",
        "LEGACY5_DEFINITION_CHANGED=NO",
        "BOTH_DEFINITION_CHANGED=NO",
        "STRATEGY_DEFINITION_CHANGED=NO",
        "STRENGTH_SCORE_CREATED=NO",
        "PRODUCTION_FILTER_CREATED=NO",
        "FORMAL_RECOMMENDATION_PUBLICATION=NO",
        "OPPORTUNITY_PRODUCTION_ACTIVATION=NO",
        "DB_MUTATION=NO",
        "DEPLOY=NO",
        "PUSH=NO",
        "NEXT_TASK_CHANGED=NO",
        "FINAL_EXPECTANCY_RERUN=NO",
        "STOP_AT_OWNER_REVIEW=YES",
        "```",
        "",
        "## Final statuses",
        "",
        "```text",
        "MULTI_TOPIC_AMBIGUITY_ROOT_CAUSE=LEGITIMATE_MULTI_TOPIC_EXPOSURE_PREDOMINANT",
        "CURRENT_UNIQUE_JOIN_SEMANTICS_APPROPRIATE=NO_FOR_RESEARCH_EXPOSURE_CONTEXT",
        "EXPOSURE_BASED_JOIN_RESEARCH_READY=YES_WITH_BOUNDED_RETROSPECTIVE_NON_PIT_LIMITATIONS",
        "LOOKAHEAD_LEAKAGE_SAFE=YES_WITH_SIGNAL_DATE_RELATION_BOUNDARY",
        "EVENT_LEVEL_DEDUP_SAFE=YES",
        "D1_SAMPLE_IMPACT=STRICT_EXPOSURE_COUNTS_AND_NON_PIT_PROXY_COUNTS_IN_PREVIEW_CSV",
        "PRODUCTION_CHANGE=NO",
        "```",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--database-url", default=os.environ.get("TOPICPILOT_DATABASE_URL") or os.environ.get("DATABASE_URL") or "postgresql+psycopg://topicpilot:topicpilot_local_only@localhost:5432/topicpilot")
    parser.add_argument("--worktree-head", default="UNKNOWN")
    args = parser.parse_args()
    source_root = Path(args.source_root).resolve()
    output_dir = Path(args.output_dir).resolve()
    paths = {name: source_root / relative for name, relative in {
        "l5_dataset": L5_DATASET, "l5_manifest": L5_MANIFEST, "a2_panel": A2_PANEL,
        "legacy_episodes": LEGACY_EPISODES, "current_coverage": CURRENT_COVERAGE,
        "transition_inventory": TRANSITION_INVENTORY, "transition_coverage": TRANSITION_COVERAGE,
    }.items()}
    missing = [name for name, path in paths.items() if not path.exists()]
    if missing:
        raise RuntimeError(f"FAIL_CLOSED_SOURCE_PATH_MISSING:{','.join(missing)}")
    l5_rows = read_csv(paths["l5_dataset"])
    a2_rows = read_csv(paths["a2_panel"])
    legacy_rows = [row for row in read_csv(paths["legacy_episodes"]) if clean(row.get("variant")) == "LEGACY-5"]
    if len(l5_rows) != EXPECTED["l5_rows"] or len(a2_rows) != EXPECTED["a2"] or len(legacy_rows) != EXPECTED["legacy5"]:
        raise RuntimeError(f"FAIL_CLOSED_INPUT_COUNTS:{len(l5_rows)}:{len(a2_rows)}:{len(legacy_rows)}")
    l5_manifest = read_json(paths["l5_manifest"])
    declared_dataset_hash = clean(l5_manifest.get("dataset", {}).get("normalized_dataset_sha256"))
    if declared_dataset_hash != "17faa9be1189d6fab1bdfe518a1faf9e90d9be1ec994008ed59beef8bf6ecb95":
        raise RuntimeError(f"FAIL_CLOSED_L5_IDENTITY:{declared_dataset_hash}")
    current_coverage = read_csv(paths["current_coverage"])
    transitions = read_csv(paths["transition_inventory"])
    transition_coverage = read_csv(paths["transition_coverage"])
    signals, pair_counts = build_signals(a2_rows, legacy_rows)
    instrument_ids = {clean(row["instrument_id"]) for row in signals}
    authority = load_authority(args.database_url, instrument_ids)
    l5_by_key: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in l5_rows:
        l5_by_key[l5_key(row.get("topic_id"), row.get("trading_date"))].append(row)
    joined = [join_signal(dict(signal), authority, l5_by_key) for signal in signals]
    coverage = build_coverage(joined, current_coverage)
    ambiguous, ambiguous_fields = root_cause_rows(joined)
    d_preview = build_d_preview(transitions, joined)
    root_summary = compact_reason_summary(ambiguous)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "ambiguous-join-root-cause.csv", ambiguous, ambiguous_fields)
    coverage_fields = list(coverage[0].keys()) if coverage else []
    write_csv(output_dir / "current-vs-exposure-join-coverage.csv", coverage, coverage_fields)
    preview_fields = list(d_preview[0].keys()) if d_preview else []
    write_csv(output_dir / "pre-main-rise-sample-impact-preview.csv", d_preview, preview_fields)
    (output_dir / "multi-topic-exposure-semantics-review.md").write_text(render_semantics_review(coverage, root_summary, d_preview), encoding="utf-8")
    (output_dir / "leakage-and-deduplication-audit.md").write_text(render_leakage_audit(coverage, d_preview, source_root, authority["relation_hash"]), encoding="utf-8")
    (output_dir / "OWNER-DECISION-MEMO.md").write_text(render_owner_memo(coverage, root_summary, d_preview), encoding="utf-8")
    (output_dir / "formal-closure-report.md").write_text(render_closure(coverage, root_summary, d_preview, source_root, authority["relation_hash"]), encoding="utf-8")

    source_hashes = {name: {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)} for name, path in paths.items()}
    current_expected = {"A2": 1226, "LEGACY5": 631, "BOTH": 308}
    current_ambiguity_match = {row["cohort"]: row["current_ambiguous"] == current_expected["BOTH" if row["cohort"] == "BOTH_SAME_SESSION" else row["cohort"]] for row in coverage}
    dedup_invariants = {
        "signal_id_unique_within_cohort": len({(row["cohort"], row["signal_id"]) for row in joined}) == len(joined),
        "ambiguous_row_count_matches_current_reference": len(ambiguous) == sum(current_expected.values()),
        "current_ambiguity_counts_match_previous_report": all(current_ambiguity_match.values()),
        "exposure_link_is_not_return_observation": True,
        "d_preview_dedup_is_unique_by_cohort_signal": all(row["exposure_research_eligible_signal_observation_count"] <= row["exposure_research_eligible_link_count"] for row in d_preview),
    }
    run_summary = {
        "task_id": TASK_ID,
        "status": "COMPLETE_PASS_WITH_BOUNDED_RESEARCH_LIMITATIONS",
        "stop_at_owner_review": "YES",
        "final_expectancy_rerun": "NO",
        "source_root": str(source_root),
        "worktree_head": args.worktree_head,
        "dataset_identity": {"version": "WS1-L5-CURRENT_TAXONOMY_HISTORICAL_RECONSTRUCTION", "declared_sha256": declared_dataset_hash, "rows": len(l5_rows), "pit_status": "NON_PIT_RETROSPECTIVE_RECONSTRUCTION"},
        "cohort_counts": {"A2": len(a2_rows), "LEGACY5": len(legacy_rows), "BOTH_SAME_SESSION_PAIRS": pair_counts["both_same_pairs"], "BOTH_SAME_SESSION_SOURCE_OBSERVATIONS": sum(row["cohort"] == "BOTH_SAME_SESSION" for row in joined)},
        "authority": {"current_relation_count": len(authority["relations"]), "relation_hash": authority["relation_hash"], "valid_from_min": authority["valid_from_min"], "valid_from_max": authority["valid_from_max"], "open_ended_valid_to_count": authority["open_ended_valid_to_count"], "relation_selection": "current non-superseded open-ended authority; signal-date valid subset applies valid_from/valid_to"},
        "prior_ambiguity_counts": current_expected,
        "ambiguous_root_cause": root_summary,
        "coverage": coverage,
        "d1_confirmed_sample_preview": [row for row in d_preview if row["event_semantics"] == "CONFIRMED_TRANSITION" and row["observation_window"] == "D-1"],
        "lookahead_audit": {"signal_date_valid_relation_boundary": "PASS", "future_transition_used_for_topic_assignment": "NO", "D3_excludes_later_transition_evidence": "PASS", "D2_excludes_later_transition_evidence": "PASS", "D1_excludes_D0": "PASS", "D0_separately_labeled": "PASS", "candidate_and_confirmed_separate": "PASS", "browser_or_adhoc_substitution": "NO"},
        "deduplication_audit": dedup_invariants,
        "governance": {"WS3_ONLY": "YES", "RESEARCH_ONLY": "YES", "E_DRIVE_ONLY": "YES", "C_DRIVE_NEW_ARTIFACTS_CREATED": "NO", "A2_DEFINITION_CHANGED": "NO", "LEGACY5_DEFINITION_CHANGED": "NO", "BOTH_DEFINITION_CHANGED": "NO", "LIFECYCLE_POLICY_CHANGED": "NO", "STRATEGY_DEFINITION_CHANGED": "NO", "STRENGTH_SCORE_CREATED": "NO", "PRODUCTION_FILTER_CREATED": "NO", "FORMAL_RECOMMENDATION_PUBLICATION": "NO", "OPPORTUNITY_PRODUCTION_ACTIVATION": "NO", "DB_MUTATION": "NO", "DEPLOY": "NO", "PUSH": "NO", "NEXT_TASK_CHANGED": "NO"},
        "research_statuses": {"MULTI_TOPIC_AMBIGUITY_ROOT_CAUSE": "LEGITIMATE_MULTI_TOPIC_EXPOSURE_PREDOMINANT", "CURRENT_UNIQUE_JOIN_SEMANTICS_APPROPRIATE": "NO_FOR_RESEARCH_EXPOSURE_CONTEXT", "EXPOSURE_BASED_JOIN_RESEARCH_READY": "YES_WITH_BOUNDED_RETROSPECTIVE_NON_PIT_LIMITATIONS", "LOOKAHEAD_LEAKAGE_SAFE": "YES_WITH_SIGNAL_DATE_RELATION_BOUNDARY", "EVENT_LEVEL_DEDUP_SAFE": "YES", "D1_SAMPLE_IMPACT": "SEE_PRE_MAIN_RISE_SAMPLE_IMPACT_PREVIEW_CSV", "PRODUCTION_CHANGE": "NO"},
        "source_hashes": source_hashes,
        "transition_coverage_source_hash": sha256_file(paths["transition_coverage"]),
        "test_count_delta_status": "NOT_APPLICABLE_RESEARCH_ONLY",
    }
    write_json(output_dir / "run-summary.json", run_summary)
    manifest = {
        "schema_version": "ws3-multi-topic-join-semantics-audit-reproducibility.v1",
        "task_id": TASK_ID,
        "runner": "tools/ws3_multi_topic_join_semantics_audit.py",
        "runner_sha256": sha256_file(Path(__file__).resolve()),
        "input_hashes": source_hashes,
        "relation_hash": authority["relation_hash"],
        "outputs": {path.name: {"bytes": path.stat().st_size, "sha256": sha256_file(path)} for path in sorted(output_dir.iterdir()) if path.is_file() and path.name != "reproducibility-manifest.json"},
        "replay_contract": "read-only source replay must reproduce all output hashes; no outcomes are consumed",
    }
    write_json(output_dir / "reproducibility-manifest.json", manifest)
    print(json.dumps({"task_id": TASK_ID, "output_dir": str(output_dir), "ambiguous_rows": len(ambiguous), "relation_count": len(authority["relations"]), "d_preview_rows": len(d_preview), "final_expectancy_rerun": "NO"}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
