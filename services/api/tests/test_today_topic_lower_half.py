from __future__ import annotations

from datetime import date, timedelta

from topicpilot_api.today_topic_lower_half import (
    build_topic_pulse,
    calculate_fast_rotation,
    rank_formal_topics,
)


def row(slug: str, *, lifecycle: str = "BASE", grade: str = "B", score: float = 50, **extra):
    value = {
        "topic_slug": slug,
        "topic_name": slug.title(),
        "snapshot_date": date(2026, 9, 29),
        "formal_member_count": 12,
        "formal_daily_grade": grade,
        "absolute_score": score,
        "relative_score": score - 1,
        "formal_lifecycle": lifecycle,
        "authority_status": "VALID",
        "authority_quality_valid": True,
        "coverage_pct": 50,
    }
    value.update(extra)
    return value


def test_mainline_uses_lifecycle_then_grade_then_candidate_then_scores_and_slug():
    rows = [
        row("base-s", lifecycle="BASE", grade="S", score=99),
        row("mature-a", lifecycle="MATURE", grade="A", score=70),
        row("mature-s", lifecycle="MATURE", grade="S", score=99),
        row("fermenting-a", lifecycle="FERMENTING", grade="A", score=70),
        row("rise-b", lifecycle="MAIN_RISE", grade="B", score=60),
        row("rise-a-no-candidate", lifecycle="MAIN_RISE", grade="A", score=60),
        row(
            "rise-a-candidate",
            lifecycle="MAIN_RISE",
            grade="A",
            score=50,
            lifecycle_candidate="MATURE",
        ),
        row("declining-s", lifecycle="DECLINING", grade="S", score=100),
    ]

    result = rank_formal_topics(rows)

    assert [item["slug"] for item in result] == [
        "rise-a-candidate",
        "rise-a-no-candidate",
        "rise-b",
    ]
    assert len(result) == 3


def test_mainline_excludes_small_sample_and_missing_authority():
    rows = [
        row("small", formal_member_count=2),
        row("missing", authority_status="NOT_EVALUABLE", authority_quality_valid=False),
        row("eligible", lifecycle="MATURE", grade="B", score=40),
    ]

    assert [item["slug"] for item in rank_formal_topics(rows)] == ["eligible"]


def test_mainline_uses_absolute_then_relative_then_coverage_then_slug_ties():
    rows = [
        row(
            "coverage-late",
            lifecycle="MATURE",
            grade="A",
            score=80,
            relative_score=70,
            coverage_pct=90,
        ),
        row(
            "relative-first",
            lifecycle="MATURE",
            grade="A",
            score=80,
            relative_score=75,
            coverage_pct=10,
        ),
        row(
            "slug-late",
            lifecycle="MATURE",
            grade="A",
            score=80,
            relative_score=75,
            coverage_pct=90,
        ),
        row(
            "slug-first",
            lifecycle="MATURE",
            grade="A",
            score=80,
            relative_score=75,
            coverage_pct=90,
        ),
    ]

    assert [item["slug"] for item in rank_formal_topics(rows)] == [
        "slug-first",
        "slug-late",
        "relative-first",
    ]


def test_topic_pulse_returns_all_topics_and_fails_closed_without_history():
    current = [
        row("stable", lifecycle="MATURE", grade="A", score=80),
        row("small", formal_member_count=2, lifecycle="MAIN_RISE", grade="S", score=90),
        row("missing", authority_status="NOT_EVALUABLE", authority_quality_valid=False),
    ]

    result = build_topic_pulse(current, [], target_date=date(2026, 9, 29))

    assert [item["slug"] for item in result] == ["stable", "missing", "small"]
    by_slug = {item["slug"]: item for item in result}
    assert by_slug["small"]["status"] == "X_NOT_FOCUS"
    assert by_slug["small"]["grade"] is None
    assert all(item["eventType"] == "NO_HISTORY" for item in result)
    assert all(item["eventTime"] is None for item in result)


def test_topic_pulse_primary_event_priority_covers_each_formal_event_type():
    target = date(2026, 9, 29)
    cases = [
        ("candidate", {"lifecycle_candidate": "MAIN_RISE"}, "LIFECYCLE_CANDIDATE"),
        ("grade", {"grade": "A"}, "GRADE_CHANGE"),
        ("divergence", {"absolute_score": 80, "relative_score": 60}, "ABS_REL_DIVERGENCE"),
        ("expansion", {"renewed_expansion": True}, "RENEWED_EXPANSION"),
        ("observation", {"observation_flags": ["NEW_FLAG"]}, "OBSERVATION_FLAG"),
        ("persistence", {}, "PERSISTENCE"),
    ]
    for slug, current_overrides, expected in cases:
        current = row(slug, **current_overrides)
        previous = row(
            slug,
            grade="B",
            snapshot_date=date(2026, 9, 26),
            lifecycle_candidate=None,
            renewed_expansion=False,
            observation_flags=[],
        )
        if expected == "GRADE_CHANGE":
            current["formal_daily_grade"] = "A"
        if expected == "PERSISTENCE":
            current["formal_daily_grade"] = previous["formal_daily_grade"]
        result = build_topic_pulse([current], [previous], target_date=target)
        assert result[0]["eventType"] == expected


def test_topic_pulse_primary_event_priority_is_deterministic():
    current = row(
        "ai",
        lifecycle="FERMENTING",
        grade="A",
        score=80,
        lifecycle_candidate="MAIN_RISE",
        candidate_confirmation_current=1,
        candidate_confirmation_required=2,
        observation_flags=["NEW_FLAG"],
    )
    previous = row(
        "ai",
        lifecycle="BASE",
        grade="B",
        score=70,
        lifecycle_candidate=None,
        candidate_confirmation_current=0,
        candidate_confirmation_required=2,
        snapshot_date=date(2026, 9, 26),
    )

    result = build_topic_pulse([current], [previous], target_date=date(2026, 9, 29))

    assert result[0]["eventType"] == "LIFECYCLE_TRANSITION"
    assert result[0]["changed"] is True
    assert "BASE → FERMENTING" in result[0]["primaryEvent"]


def test_fast_rotation_uses_previous_five_session_median_current_excluded_and_returns_all():
    target = date(2026, 9, 29)
    prior_dates = [target - timedelta(days=offset) for offset in range(5, 0, -1)]
    rows = []
    for index, session in enumerate(prior_dates):
        rows.extend(
            [
                row("warm", snapshot_date=session, score=50 + index),
                row("cool", snapshot_date=session, score=100 - index),
                row("outlier", snapshot_date=session, score=0 if index == 0 else 50),
            ]
        )
    rows.extend(
        [
            row("warm", snapshot_date=target, score=64),
            row("cool", snapshot_date=target, score=88),
            row("outlier", snapshot_date=target, score=60),
        ]
    )

    warming, cooling, reason = calculate_fast_rotation(rows, target_date=target)

    assert reason is None
    assert [item["topicSlug"] for item in warming] == ["warm", "outlier"]
    assert [item["topicSlug"] for item in cooling] == ["cool"]
    assert warming[0]["strengthDelta"] == 12  # prior median is 52; current is 64
    assert cooling[0]["strengthDelta"] == -10  # prior median is 98; current is 88


def test_fast_rotation_thresholds_and_startup_fail_closed():
    target = date(2026, 9, 29)
    dates = [target - timedelta(days=offset) for offset in range(5, 0, -1)]
    rows = [row("warm", snapshot_date=session, score=50) for session in dates]
    rows += [row("cool", snapshot_date=session, score=50) for session in dates]
    rows += [
        row("warm", snapshot_date=target, score=60),
        row("cool", snapshot_date=target, score=40),
    ]

    warming, cooling, reason = calculate_fast_rotation(rows, target_date=target)
    assert reason is None
    assert [item["topicSlug"] for item in warming] == ["warm"]
    assert [item["topicSlug"] for item in cooling] == ["cool"]

    short = [item for item in rows if item["snapshot_date"] != dates[0]]
    assert (
        calculate_fast_rotation(short, target_date=target)[2]
        == "INSUFFICIENT_FORMAL_STRENGTH_HISTORY"
    )


def test_fast_rotation_distinguishes_missing_current_formal_strength_from_short_history():
    target = date(2026, 9, 29)
    prior_dates = [target - timedelta(days=offset) for offset in range(5, 0, -1)]
    rows = [row("warm", snapshot_date=session, score=50) for session in prior_dates]

    warming, cooling, reason = calculate_fast_rotation(rows, target_date=target)

    assert warming == []
    assert cooling == []
    assert reason == "CURRENT_FORMAL_TOPIC_STRENGTH_NOT_PUBLISHED"
