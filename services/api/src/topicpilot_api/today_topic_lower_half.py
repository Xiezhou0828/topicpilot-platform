"""Formal, deterministic read logic for the lower half of Today.

This module is intentionally policy-free.  Topic Strength and Lifecycle are
owned by their persisted formal results; this module only applies the frozen
Today presentation contracts to already-authoritative rows.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from datetime import date
from statistics import median
from typing import Any

MAINLINE_LIFECYCLE_PRIORITY = {
    "MAIN_RISE": 0,
    "FERMENTING": 1,
    "MATURE": 2,
    "SPROUTING": 3,
    "BASE": 4,
}
GRADE_PRIORITY = {"S": 0, "A": 1, "B": 2, "D": 3}
ROTATION_HISTORY_SESSIONS = 5
FAST_WARMING_THRESHOLD = 10.0
FAST_COOLING_THRESHOLD = -10.0
MIN_FORMAL_MEMBERS = 3

EVENT_PRIORITY = {
    "LIFECYCLE_TRANSITION": 0,
    "LIFECYCLE_CANDIDATE": 1,
    "GRADE_CHANGE": 2,
    "ABS_REL_DIVERGENCE": 3,
    "RENEWED_EXPANSION": 4,
    "OBSERVATION_FLAG": 5,
    "PERSISTENCE": 6,
    "NO_HISTORY": 7,
}


def _number(value: Any) -> float | int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return int(result) if result.is_integer() else result


def _finite(value: Any) -> float | None:
    number = _number(value)
    return float(number) if number is not None else None


def _slug(row: Mapping[str, Any]) -> str:
    return str(row.get("topic_slug") or row.get("slug") or "")


def _name(row: Mapping[str, Any]) -> str:
    return str(row.get("topic_name") or row.get("name") or _slug(row))


def _grade(row: Mapping[str, Any]) -> str | None:
    value = row.get("formal_daily_grade", row.get("formal_grade"))
    return str(value) if value in GRADE_PRIORITY else None


def _lifecycle(row: Mapping[str, Any]) -> str | None:
    value = row.get("formal_lifecycle", row.get("lifecycle"))
    return str(value) if isinstance(value, str) and value else None


def _candidate(row: Mapping[str, Any]) -> str | None:
    value = row.get("lifecycle_candidate", row.get("candidate_stage"))
    return str(value) if isinstance(value, str) and value else None


def _absolute_score(row: Mapping[str, Any]) -> float | None:
    return _finite(row.get("absolute_score"))


def _relative_score(row: Mapping[str, Any]) -> float | None:
    return _finite(row.get("relative_score"))


def _member_count(row: Mapping[str, Any]) -> int | None:
    for key in ("formal_member_count", "eligible_count", "stock_count"):
        value = row.get(key)
        if value is not None:
            try:
                return int(value)
            except (TypeError, ValueError):
                return None
    return None


def _coverage(row: Mapping[str, Any]) -> float | None:
    return _finite(row.get("formal_coverage_pct", row.get("coverage_pct")))


def _authority_valid(row: Mapping[str, Any]) -> bool:
    explicit = row.get("authority_quality_valid")
    if isinstance(explicit, bool):
        return explicit
    return row.get("authority_status") == "VALID"


def _evaluable(row: Mapping[str, Any]) -> bool:
    return bool(
        _member_count(row) is not None
        and (_member_count(row) or 0) >= MIN_FORMAL_MEMBERS
        and _grade(row) is not None
        and _lifecycle(row) is not None
        and _absolute_score(row) is not None
        and _authority_valid(row)
    )


def _candidate_present(row: Mapping[str, Any]) -> bool:
    candidate = _candidate(row)
    lifecycle = _lifecycle(row)
    return bool(candidate and candidate != lifecycle and row.get("candidate_valid", True) is not False)


def _rank_tuple(row: Mapping[str, Any]) -> tuple[Any, ...]:
    lifecycle = _lifecycle(row)
    grade = _grade(row)
    absolute = _absolute_score(row)
    relative = _relative_score(row)
    coverage = _coverage(row)
    return (
        MAINLINE_LIFECYCLE_PRIORITY.get(lifecycle or "", 99),
        GRADE_PRIORITY.get(grade or "", 99),
        0 if _candidate_present(row) else 1,
        -(absolute if absolute is not None else float("-inf")),
        -(relative if relative is not None else float("-inf")),
        -(coverage if coverage is not None else float("-inf")),
        _slug(row),
    )


def _event_divergence(row: Mapping[str, Any]) -> bool:
    absolute = _absolute_score(row)
    relative = _relative_score(row)
    if absolute is None or relative is None:
        return False
    absolute_grade = row.get("absolute_grade")
    relative_grade = row.get("relative_grade")
    return bool(
        (absolute_grade and relative_grade and absolute_grade != relative_grade)
        or abs(absolute - relative) >= 10.0
    )


def _new_observation_flags(current: Mapping[str, Any], previous: Mapping[str, Any] | None) -> bool:
    current_flags = set(current.get("observation_flags") or ())
    previous_flags = set(previous.get("observation_flags") or ()) if previous else set()
    return bool(current_flags - previous_flags)


def _confirmation(row: Mapping[str, Any]) -> dict[str, Any] | None:
    value = row.get("confirmation_progress")
    if isinstance(value, Mapping):
        return dict(value)
    candidate = _candidate(row)
    if candidate is None:
        return None
    current = row.get("candidate_confirmation_current", row.get("candidate_streak"))
    required = row.get("candidate_confirmation_required")
    result = {"candidate": candidate}
    if current is not None:
        result["current"] = current
    if required is not None:
        result["required"] = required
    return result


def _topic_payload(row: Mapping[str, Any], *, rank: int | None = None) -> dict[str, Any]:
    grade = _grade(row)
    lifecycle = _lifecycle(row)
    absolute = _absolute_score(row)
    relative = _relative_score(row)
    member_count = _member_count(row)
    small_sample = member_count is not None and member_count < MIN_FORMAL_MEMBERS
    status = "X_NOT_FOCUS" if small_sample else "EVALUABLE" if _evaluable(row) else "NOT_EVALUABLE"
    if status != "EVALUABLE":
        grade = None
        lifecycle = None
        absolute = None
        relative = None
    payload = {
        "slug": _slug(row),
        "name": _name(row),
        "grade": grade,
        "strength": absolute,
        "currentState": None,
        "stockCount": member_count or 0,
        "summary": _summary(row, status=status, grade=grade, lifecycle=lifecycle, absolute=absolute),
        "favorite": False,
        "dataDate": row.get("snapshot_date") or row.get("evaluation_date"),
        "absoluteScore": absolute,
        "relativeScore": relative,
        "lifecycle": lifecycle,
        "lifecycleCandidate": _candidate(row) if status == "EVALUABLE" else None,
        "candidateConfirmation": _confirmation(row) if status == "EVALUABLE" else None,
        "formalMemberCount": member_count,
        "coveragePct": _coverage(row),
        "authorityStatus": row.get("authority_status") or ("VALID" if _authority_valid(row) else "NOT_EVALUABLE"),
        "topicStatus": status,
        "rankingEvidence": {
            "rankingPolicy": "lifecycle,grade,candidate,absoluteScore,relativeScore,coverage,slug",
            "absoluteScore": absolute,
            "relativeScore": relative,
            "formalMemberCount": member_count,
            "coveragePct": _coverage(row),
        },
    }
    if rank is not None:
        payload["rank"] = rank
    return payload


def _summary(
    row: Mapping[str, Any],
    *,
    status: str,
    grade: str | None,
    lifecycle: str | None,
    absolute: float | None,
) -> str:
    if status == "X_NOT_FOCUS":
        return "正式成員不足 3 檔，X／暫不關注。"
    if status != "EVALUABLE":
        return "正式 Topic Strength／Lifecycle authority 尚未完整。"
    candidate = _candidate(row)
    candidate_text = f"；{candidate} candidate" if candidate and candidate != lifecycle else ""
    return f"{grade} · {lifecycle} · 絕對強度 {_number(absolute)}{candidate_text}。"


def rank_formal_topics(rows: Iterable[Mapping[str, Any]], limit: int = 3) -> list[dict[str, Any]]:
    """Select the structurally relevant current formal Topics for Mainline."""

    eligible = [row for row in rows if _evaluable(row) and _lifecycle(row) != "DECLINING"]
    ordered = sorted(eligible, key=_rank_tuple)[: max(0, limit)]
    return [_topic_payload(row, rank=index + 1) for index, row in enumerate(ordered)]


def _primary_event(
    current: Mapping[str, Any], previous: Mapping[str, Any] | None
) -> tuple[str, str, bool]:
    if previous is None:
        return "NO_HISTORY", "初始狀態；尚無可比對的正式歷史。", False
    current_lifecycle = _lifecycle(current)
    previous_lifecycle = _lifecycle(previous)
    if current_lifecycle and previous_lifecycle and current_lifecycle != previous_lifecycle:
        return (
            "LIFECYCLE_TRANSITION",
            f"{previous_lifecycle} → {current_lifecycle}",
            True,
        )
    if (
        _candidate(current) != _candidate(previous)
        or current.get("candidate_confirmation_current") != previous.get("candidate_confirmation_current")
        or current.get("candidate_confirmation_required") != previous.get("candidate_confirmation_required")
    ) and (_candidate(current) or _candidate(previous)):
        confirmation = _confirmation(current)
        progress = ""
        if confirmation and confirmation.get("current") is not None and confirmation.get("required") is not None:
            progress = f" · {confirmation['current']} / {confirmation['required']}"
        return "LIFECYCLE_CANDIDATE", f"{_candidate(current) or _candidate(previous)} candidate{progress}", True
    if _grade(current) != _grade(previous) and (_grade(current) or _grade(previous)):
        return "GRADE_CHANGE", f"Grade {_grade(previous) or '—'} → {_grade(current) or '—'}", True
    current_divergence = _event_divergence(current)
    previous_divergence = _event_divergence(previous)
    current_gap = abs((_absolute_score(current) or 0) - (_relative_score(current) or 0))
    previous_gap = abs((_absolute_score(previous) or 0) - (_relative_score(previous) or 0))
    if current_divergence and (not previous_divergence or abs(current_gap - previous_gap) >= 10.0):
        return "ABS_REL_DIVERGENCE", "絕對／相對強度分歧", True
    if current.get("renewed_expansion") is True and previous.get("renewed_expansion") is not True:
        return "RENEWED_EXPANSION", "重新擴張", True
    if _new_observation_flags(current, previous):
        return "OBSERVATION_FLAG", "新增觀察旗標", True
    streak = current.get("persistence_days")
    streak_text = f"延續第 {streak} 日" if streak is not None else "狀態延續"
    return "PERSISTENCE", streak_text, False


def build_topic_pulse(
    rows: Iterable[Mapping[str, Any]],
    history: Iterable[Mapping[str, Any]],
    *,
    target_date: date,
) -> list[dict[str, Any]]:
    """Return every current formal Topic, with one deterministic primary event."""

    previous_by_slug: dict[str, Mapping[str, Any]] = {}
    for row in history:
        if row.get("snapshot_date") == target_date or row.get("evaluation_date") == target_date:
            continue
        slug = _slug(row)
        if not slug:
            continue
        row_date = row.get("snapshot_date") or row.get("evaluation_date")
        prior_date = previous_by_slug.get(slug, {}).get("snapshot_date") or previous_by_slug.get(slug, {}).get("evaluation_date")
        if prior_date is None or (row_date is not None and row_date > prior_date):
            previous_by_slug[slug] = row

    result: list[dict[str, Any]] = []
    for row in rows:
        slug = _slug(row)
        previous = previous_by_slug.get(slug)
        event_type, event_copy, changed = _primary_event(row, previous)
        item = _topic_payload(row)
        item.update(
            {
                "dataDate": row.get("snapshot_date") or row.get("evaluation_date") or target_date,
                "eventTime": None,
                "eventType": event_type,
                "primaryEvent": event_copy,
                "changed": changed,
                "eventSource": "FORMAL_TOPIC_STATE_COMPARISON" if previous else "FORMAL_TOPIC_STATE_NO_HISTORY",
                "eventEvidence": {
                    "hasComparableHistory": previous is not None,
                    "secondaryEvents": [],
                },
            }
        )
        result.append(item)

    def pulse_key(item: Mapping[str, Any]) -> tuple[Any, ...]:
        lifecycle = item.get("lifecycle")
        grade = item.get("grade")
        absolute = _finite(item.get("absoluteScore"))
        return (
            0 if item.get("changed") else 1,
            EVENT_PRIORITY.get(str(item.get("eventType")), 99),
            MAINLINE_LIFECYCLE_PRIORITY.get(str(lifecycle), 99),
            GRADE_PRIORITY.get(str(grade), 99),
            -(absolute if absolute is not None else float("-inf")),
            str(item.get("slug") or ""),
        )

    return sorted(result, key=pulse_key)


def calculate_fast_rotation(
    rows: Iterable[Mapping[str, Any]],
    *,
    target_date: date,
    history_sessions: int = ROTATION_HISTORY_SESSIONS,
    warming_threshold: float = FAST_WARMING_THRESHOLD,
    cooling_threshold: float = FAST_COOLING_THRESHOLD,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str | None]:
    """Compare current absolute strength to each Topic's prior 5-session median."""

    usable = [
        row
        for row in rows
        if _evaluable(row)
        and (row.get("snapshot_date") or row.get("evaluation_date")) is not None
        and _absolute_score(row) is not None
    ]
    current_rows = {
        _slug(row): row
        for row in usable
        if (row.get("snapshot_date") or row.get("evaluation_date")) == target_date
    }
    prior_sessions = sorted(
        {
            row.get("snapshot_date") or row.get("evaluation_date")
            for row in usable
            if (row.get("snapshot_date") or row.get("evaluation_date")) < target_date
        }
    )
    if len(prior_sessions) < history_sessions:
        return [], [], "INSUFFICIENT_FORMAL_STRENGTH_HISTORY"
    baseline_sessions = prior_sessions[-history_sessions:]
    by_topic: dict[str, dict[date, Mapping[str, Any]]] = {}
    for row in usable:
        row_date = row.get("snapshot_date") or row.get("evaluation_date")
        if row_date in baseline_sessions:
            by_topic.setdefault(_slug(row), {})[row_date] = row

    warming: list[dict[str, Any]] = []
    cooling: list[dict[str, Any]] = []
    for slug, current in current_rows.items():
        prior = by_topic.get(slug, {})
        if any(session not in prior for session in baseline_sessions):
            continue
        baseline_values = [_absolute_score(prior[session]) for session in baseline_sessions]
        if any(value is None for value in baseline_values):
            continue
        current_score = _absolute_score(current)
        baseline = float(median(value for value in baseline_values if value is not None))
        assert current_score is not None
        delta = current_score - baseline
        if delta < cooling_threshold and delta > warming_threshold:
            continue
        direction = "warming" if delta >= warming_threshold else "cooling" if delta <= cooling_threshold else None
        if direction is None:
            continue
        lifecycle = _lifecycle(current)
        grade = _grade(current)
        copy = (
            f"{lifecycle}/{grade} · 題材仍在早期，但短期強度快速提升。"
            if direction == "warming" and lifecycle in {"BASE", "SPROUTING"}
            else f"{lifecycle}/{grade} · 既有主線再度升溫，強勢結構持續。"
            if direction == "warming"
            else f"{lifecycle}/{grade} · 題材仍屬主線，但短期強度明顯降溫。"
            if lifecycle == "MAIN_RISE"
            else f"{lifecycle}/{grade} · 成熟題材近期強度進一步轉弱。"
            if direction == "cooling" and lifecycle == "MATURE"
            else f"{lifecycle}/{grade} · 短期正式強度{'提升' if direction == 'warming' else '轉弱'}。"
        )
        item = {
            "topic": _name(current),
            "topicSlug": slug,
            "strengthDelta": delta,
            "currentGrade": grade,
            "lifecycle": lifecycle,
            "absoluteScore": current_score,
            "baselineMedian": baseline,
            "baselineSessions": baseline_sessions,
            "averageDailyChange": None,
            "observedStockCount": _member_count(current),
            "summary": copy,
            "dataDate": target_date,
            "asOf": current.get("as_of_at"),
            "rotationEvidence": {
                "measure": "formal absolute Topic Strength score",
                "baseline": "previous 5 governed/evaluable trading sessions median",
                "baselineSessions": baseline_sessions,
                "threshold": warming_threshold if direction == "warming" else cooling_threshold,
            },
        }
        (warming if direction == "warming" else cooling).append(item)

    warming.sort(key=lambda item: (-item["strengthDelta"], item["topicSlug"]))
    cooling.sort(key=lambda item: (item["strengthDelta"], item["topicSlug"]))
    return warming, cooling, None


__all__ = [
    "FAST_COOLING_THRESHOLD",
    "FAST_WARMING_THRESHOLD",
    "MAINLINE_LIFECYCLE_PRIORITY",
    "build_topic_pulse",
    "calculate_fast_rotation",
    "rank_formal_topics",
]
