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
