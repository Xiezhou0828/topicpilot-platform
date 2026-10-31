from datetime import UTC, datetime, timedelta

import pytest

from topicpilot_api.company_profile_v4.store import approval_content_sha256
from topicpilot_api.stock_add_master_writer import (
    PLAN_SCHEMA,
    StockAddWriterError,
    canonical_sha256,
    dry_run_master_add,
    expected_confirmation,
    validate_master_plan,
)


def _approved_package() -> dict:
    package = {
        "packageVersion": "topicpilot-stock-research.v4",
        "company": {
            "stockCode": "2468",
            "displayName": "華經",
            "legalName": "華經資訊企業股份有限公司",
            "market": "TPE",
            "instrumentType": "EQUITY",
            "currency": "TWD",
        },
        "researchMetadata": {"researchAsOf": "2026-10-25"},
        "overviewData": {"businessModel": {"shortDesc": "企業資訊系統整合與服務。"}},
        "sections": {},
        "frontendProjection": {
            "contractVersion": "company-research-frontend.v4",
            "researchGovernance": {
                "dataCompletenessScore": 1.0,
                "confidenceLevel": "HIGH",
                "hasUnresolvedGaps": False,
                "publication": {
                    "publicationStatus": "PUBLISHED",
                    "ownerReviewStatus": "APPROVED",
                    "sourceRightsStatus": "APPROVED",
                    "approvalEvidence": {
                        "decisionId": "review-2468-1",
                        "reviewer": "owner",
                        "approvedAt": "2026-10-31T07:00:00Z",
                        "packageSha256": "",
                    },
                },
            },
            "investmentThemes": [],
            "operatingMatrix": [],
            "limitationsZhTw": [],
        },
    }
    package["frontendProjection"]["researchGovernance"]["publication"]["approvalEvidence"][
        "packageSha256"
    ] = approval_content_sha256(package)
    return package


def _plan() -> dict:
    plan = {
        "schemaVersion": PLAN_SCHEMA,
        "stock": {
            "market": "TPE",
            "stockCode": "2468",
            "name": "華經",
            "instrumentType": "EQUITY",
            "currency": "TWD",
            "validFrom": "2026-10-25",
            "validFromEvidenceUrl": "https://www.twse.com.tw/zh/",
        },
        "researchPackage": _approved_package(),
        "masterReadback": {
            "status": "NO_MATCH_CONFIRMED",
            "source": "TopicPilot protected Production catalog readback",
            "environment": "PRODUCTION_READ_ONLY",
            "readAt": datetime.now(UTC).isoformat(),
            "complete": True,
            "sha256": "c" * 64,
        },
    }
    plan["planSha256"] = canonical_sha256(plan)
    return plan


def _reseal(plan: dict) -> None:
    plan["planSha256"] = canonical_sha256(
        {key: value for key, value in plan.items() if key != "planSha256"}
    )


class _ScalarResult:
    def __init__(self, value):
        self.value = value

    def scalar_one(self):
        return self.value


class _RowResult:
    def __init__(self, row):
        self.row = row

    def mappings(self):
        return self

    def first(self):
        return self.row


class _DryRunConnection:
    def __init__(self, existing=None):
        self.existing = existing
        self.statements = []

    def execute(self, statement, params=None):
        sql = str(statement)
        self.statements.append(sql)
        if "SELECT i.id, i.name" in sql:
            return _RowResult(self.existing)
        if "SELECT id FROM topicpilot.markets" in sql:
            return _RowResult({"id": "market-id"})
        if "SELECT id, publication_version" in sql:
            return _RowResult(None)
        if "SELECT COALESCE(MAX(publication_version)" in sql:
            return _ScalarResult(0)
        raise AssertionError(f"Unexpected dry-run query: {sql}")


def test_valid_no_match_plan_is_a_normal_add_instrument_candidate():
    plan = _plan()
    payload, digest, operation_id = validate_master_plan(plan)

    assert payload["masterReadback"]["status"] == "NO_MATCH_CONFIRMED"
    assert digest == plan["planSha256"]
    assert operation_id == f"stock-add:master:TPE:2468:{digest}"
    assert expected_confirmation("TPE", "2468", digest) == (f"APPLY STOCK ADD TPE 2468 {digest}")


def test_valid_match_readback_is_a_normal_research_update_candidate():
    plan = _plan()
    plan["masterReadback"]["status"] = "MATCH_FOUND"
    _reseal(plan)

    payload, digest, _ = validate_master_plan(plan)

    assert payload["masterReadback"]["status"] == "MATCH_FOUND"
    assert digest == plan["planSha256"]


def test_dry_run_routes_existing_stock_to_research_publication_only():
    plan = _plan()
    plan["masterReadback"]["status"] = "MATCH_FOUND"
    _reseal(plan)
    connection = _DryRunConnection(
        {
            "id": "existing-instrument-id",
            "name": plan["stock"]["name"],
            "instrument_type": "EQUITY",
            "currency": "TWD",
            "valid_from": None,
            "is_active": True,
        }
    )

    result = dry_run_master_add(connection, plan)

    assert result.action == "PUBLISH_RESEARCH_UPDATE"
    assert result.created is False
    assert "instruments" not in result.to_dict()["writeSet"]
    assert not any(statement.lstrip().startswith("INSERT") for statement in connection.statements)


def test_dry_run_routes_missing_stock_to_add_and_publish():
    plan = _plan()
    connection = _DryRunConnection()

    result = dry_run_master_add(connection, plan)

    assert result.action == "ADD_INSTRUMENT_AND_PUBLISH"
    assert result.created is False
    assert not any(statement.lstrip().startswith("INSERT") for statement in connection.statements)


def test_plan_digest_change_is_rejected():
    plan = _plan()
    plan["stock"]["name"] = "華經資訊"
    plan["researchPackage"]["company"]["displayName"] = plan["stock"]["name"]
    plan["researchPackage"]["frontendProjection"]["researchGovernance"]["publication"][
        "approvalEvidence"
    ]["packageSha256"] = approval_content_sha256(plan["researchPackage"])

    with pytest.raises(StockAddWriterError, match="PLAN_SHA256_MISMATCH"):
        validate_master_plan(plan)


def test_partial_research_package_cannot_be_written():
    plan = _plan()
    plan["researchPackage"]["frontendProjection"]["researchGovernance"]["publication"][
        "ownerReviewStatus"
    ] = "PENDING"
    plan["researchPackage"]["frontendProjection"]["researchGovernance"]["publication"][
        "approvalEvidence"
    ]["packageSha256"] = approval_content_sha256(plan["researchPackage"])
    plan["planSha256"] = canonical_sha256(
        {key: value for key, value in plan.items() if key != "planSha256"}
    )

    with pytest.raises(StockAddWriterError, match="RESEARCH_PACKAGE_NOT_OWNER_APPROVED"):
        validate_master_plan(plan)


def test_stale_master_readback_cannot_authorize_a_write():
    plan = _plan()
    plan["masterReadback"]["readAt"] = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
    plan["planSha256"] = canonical_sha256(
        {key: value for key, value in plan.items() if key != "planSha256"}
    )

    with pytest.raises(StockAddWriterError, match="MASTER_READBACK_STALE"):
        validate_master_plan(plan)


def test_only_confirmed_full_market_absence_is_accepted():
    plan = _plan()
    plan["masterReadback"]["status"] = "RETRIEVAL_BLOCKED"
    plan["planSha256"] = canonical_sha256(
        {key: value for key, value in plan.items() if key != "planSha256"}
    )

    with pytest.raises(StockAddWriterError, match="MASTER_READBACK_NOT_COMPLETE"):
        validate_master_plan(plan)
