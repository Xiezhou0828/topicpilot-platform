from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import topicpilot_api.stock_add_authority_cli as cli
from topicpilot_api.stock_add_authority import PROTECTED_DB_SOURCE, FormalAuthoritySnapshot
from topicpilot_api.stock_add_workflow import AuthorityReadEvidence, canonical_sha256


def _snapshot() -> FormalAuthoritySnapshot:
    now = datetime.now(UTC).isoformat()
    return FormalAuthoritySnapshot(
        stock_items=(
            {
                "instrumentId": "internal-instrument-id",
                "code": "2468",
                "name": "華經資訊",
                "market": "TPE",
            },
        ),
        topic_items=(
            {
                "topicId": "internal-topic-id",
                "slug": "formal-topic",
                "name": "正式題材",
                "enabled": True,
            },
        ),
        master_evidence=AuthorityReadEvidence(
            source=PROTECTED_DB_SOURCE,
            environment="PRODUCTION_READ_ONLY",
            read_at=now,
            complete=True,
            sha256="a" * 64,
            record_count=520,
            page_count=1,
            scope="all TPE/TWO equities",
        ),
        topic_catalog_evidence=AuthorityReadEvidence(
            source=PROTECTED_DB_SOURCE,
            environment="PRODUCTION_READ_ONLY",
            read_at=now,
            complete=True,
            sha256="b" * 64,
            record_count=132,
            page_count=1,
            scope="complete formal topic catalog",
            as_of="2026-10-25",
        ),
        read_controls={
            "databaseRole": "topicpilot_catalog_readonly",
            "databaseTargetVerified": True,
            "transactionReadOnly": True,
            "transactionIsolation": "repeatable read",
            "mutationPrivilegesObserved": False,
            # Effective TEMP may be inherited from the standard PUBLIC grant;
            # the protected check is that the role has no direct DB mutation grant.
            "directDatabaseMutationPrivilegeObserved": False,
            "effectiveTemporaryPrivilegeObserved": True,
            "activeMarketCodes": ["TPE", "TWO"],
            "migrationHead": "0099",
        },
    )


def test_authority_readback_report_is_aggregate_and_hash_bound() -> None:
    report = cli.build_readback_report(
        stock_code="2468",
        market="TPE",
        source_revision="a" * 40,
        snapshot=_snapshot(),
    )

    digest = report.pop("authorityReadbackSha256")
    assert digest == canonical_sha256(report)
    assert report["stockMaster"]["status"] == "MATCH_FOUND"
    assert report["stockMaster"]["targetMatchCount"] == 1
    assert report["topicCatalog"]["status"] == "READY"
    assert "stockItems" not in report
    assert "topicItems" not in report
    assert "internal-instrument-id" not in json.dumps(report)
    assert "internal-topic-id" not in json.dumps(report)
    assert report["topicNameCandidateReadback"] == {
        "status": "NOT_REQUESTED",
        "searchTerms": [],
        "matches": [],
    }


def test_topic_name_search_returns_only_bounded_public_fields() -> None:
    snapshot = _snapshot()
    report = cli.build_readback_report(
        stock_code="2468",
        market="TPE",
        source_revision="a" * 40,
        snapshot=snapshot,
        topic_search_terms=("正式",),
    )

    result = report["topicNameCandidateReadback"]
    assert result["status"] == "MATCHES_RETURNED"
    assert result["matchCount"] == 1
    assert result["matches"] == [
        {
            "slug": "formal-topic",
            "name": "正式題材",
            "status": None,
            "parentNames": [],
            "matchedTerms": ["正式"],
            "decisionStatus": "NAME_MATCH_REQUIRES_EVIDENCE_REVIEW",
        }
    ]
    assert "internal-topic-id" not in json.dumps(result)
    assert result["matches"][0]["decisionStatus"] != "RELATION_CANDIDATE"


def test_topic_name_search_fails_closed_when_too_broad() -> None:
    snapshot = replace(
        _snapshot(),
        topic_items=tuple(
            {
                "topicId": f"private-{index}",
                "slug": f"cloud-{index}",
                "name": f"雲端服務{index}",
                "enabled": True,
            }
            for index in range(cli.MAX_TOPIC_CANDIDATE_MATCHES + 1)
        ),
    )

    result = cli._topic_name_candidates(snapshot, ("雲端",))

    assert result["status"] == "TOO_BROAD"
    assert result["matches"] == []
    assert result["matchCount"] == cli.MAX_TOPIC_CANDIDATE_MATCHES + 1


def test_topic_name_search_excludes_topics_without_current_effective_status() -> None:
    snapshot = replace(
        _snapshot(),
        topic_items=(
            {"topicId": "unknown", "slug": "cloud-unknown", "name": "雲端未知"},
            {
                "topicId": "inactive",
                "slug": "cloud-inactive",
                "name": "雲端停用",
                "enabled": False,
            },
            {
                "topicId": "active",
                "slug": "cloud-active",
                "name": "雲端有效",
                "enabled": True,
            },
        ),
    )

    result = cli._topic_name_candidates(snapshot, ("雲端",))

    assert result["status"] == "MATCHES_RETURNED"
    assert [row["slug"] for row in result["matches"]] == ["cloud-active"]


def test_topic_search_terms_are_validated_before_read(monkeypatch, capsys) -> None:
    revision = "a" * 40
    monkeypatch.setenv("GITHUB_SHA", revision)
    monkeypatch.setattr(
        cli,
        "read_protected_database_authority_snapshot",
        lambda **_: (_ for _ in ()).throw(AssertionError("database must not be read")),
    )

    result = cli.main(
        [
            "2468",
            "--market",
            "TPE",
            "--source-revision",
            revision,
            "--topic-search-terms",
            "not-json",
        ]
    )

    assert result == 2
    assert capsys.readouterr().err.strip() == "TOPIC_SEARCH_TERMS_MUST_BE_JSON_ARRAY"


def test_github_summary_values_are_plain_text_and_single_line() -> None:
    value = "雲端`**[名稱]**\n<script>|_~\\"

    assert cli.safe_github_summary_text(value) == (
        "雲端&#96;&#42;&#42;&#91;名稱&#93;&#42;&#42; &lt;script&gt;&#124;&#95;&#126;&#92;"
    )


def test_authority_readback_cli_does_not_require_a_research_package(monkeypatch, capsys) -> None:
    revision = "a" * 40
    monkeypatch.setenv("GITHUB_SHA", revision)
    monkeypatch.setattr(cli, "read_protected_database_authority_snapshot", lambda **_: _snapshot())

    result = cli.main(["2468", "--market", "TPE", "--source-revision", revision])

    assert result == 0
    report = json.loads(capsys.readouterr().out)
    assert report["mode"] == "PROTECTED_READ_ONLY_AUTHORITY_CHECK"
    assert report["stockMaster"]["status"] == "MATCH_FOUND"
    assert report["productionMutation"] is False
    assert report["writesPerformed"] == []


def test_authority_readback_cli_rejects_a_different_dispatch_revision(monkeypatch, capsys) -> None:
    monkeypatch.setenv("GITHUB_SHA", "b" * 40)
    result = cli.main(["2468", "--market", "TPE", "--source-revision", "a" * 40])

    assert result == 2
    assert capsys.readouterr().err.strip() == "SOURCE_REVISION_MISMATCH_DISPATCHED_SHA"


def test_authority_readback_cli_rejects_stale_authority(monkeypatch, capsys) -> None:
    revision = "a" * 40
    monkeypatch.setenv("GITHUB_SHA", revision)
    snapshot = _snapshot()
    stale_master = replace(
        snapshot.master_evidence,
        read_at=(datetime.now(UTC) - timedelta(minutes=16)).isoformat(),
    )
    monkeypatch.setattr(
        cli,
        "read_protected_database_authority_snapshot",
        lambda **_: replace(snapshot, master_evidence=stale_master),
    )

    result = cli.main(["2468", "--market", "TPE", "--source-revision", revision])

    assert result == 2
    assert capsys.readouterr().err.strip() == "PRODUCTION_CATALOG_READBACK_NOT_CURRENT"


def test_authority_readback_cli_rejects_unverified_direct_database_privileges(
    monkeypatch, capsys
) -> None:
    revision = "a" * 40
    monkeypatch.setenv("GITHUB_SHA", revision)
    snapshot = _snapshot()
    controls = dict(snapshot.read_controls or {})
    controls["directDatabaseMutationPrivilegeObserved"] = True
    monkeypatch.setattr(
        cli,
        "read_protected_database_authority_snapshot",
        lambda **_: replace(snapshot, read_controls=controls),
    )

    result = cli.main(["2468", "--market", "TPE", "--source-revision", revision])

    assert result == 2
    assert capsys.readouterr().err.strip() == "PRODUCTION_CATALOG_READ_CONTROLS_INCOMPLETE"
