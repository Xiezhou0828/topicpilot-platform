from __future__ import annotations

import hashlib
import json
from contextlib import nullcontext

from fastapi.testclient import TestClient

from topicpilot_api.company_profile_v4.contract import CompanyResearchV4PublicResponse
from topicpilot_api.company_profile_v4.database_store import DatabaseCompanyProfileV4ReadStore
from topicpilot_api.company_profile_v4.store import FileCompanyProfileV4ReadStore
from topicpilot_api.config import Settings
from topicpilot_api.main import create_app


class _FakeResult:
    def __init__(self, *, scalar=None, row=None):
        self.scalar = scalar
        self.row = row

    def scalar_one(self):
        return self.scalar

    def mappings(self):
        return self

    def one(self):
        return self.row

    def first(self):
        return self.row


class _FakeSession:
    def __init__(self, results):
        self.results = iter(results)

    def execute(self, statement, params=None):
        return next(self.results)


def package(
    *,
    owner_status: str = "APPROVED",
    completeness: float = 0.72,
    source_rights: str = "APPROVED",
    publication_status: str = "PUBLISHED",
) -> dict:
    result = {
        "packageVersion": "topicpilot-stock-research.v4",
        "company": {"stockCode": "2468", "displayName": "華經"},
        "researchMetadata": {"researchAsOf": "2026-10-25"},
        "sourceRegister": [{"evidenceId": "PRIVATE-EVIDENCE", "url": "https://example.test"}],
        "overviewData": {
            "businessModel": {
                "shortDesc": "企業資訊系統整合與服務。",
                "sourceEvidenceIds": ["PRIVATE-EVIDENCE"],
            }
        },
        "sections": {
            "companyAndBusiness": {
                "summary": "提供資訊系統整合服務。",
                "sourceEvidenceIds": ["PRIVATE-EVIDENCE"],
            },
            "productsAndMarket": {
                "summary": "專案型系統整合與維運服務。",
                "revenueMixPeriod": "2025 FY",
                "revenueMix": [
                    {
                        "category": "系統整合",
                        "value": 21.0,
                        "unit": "TWD_100_MILLION",
                        "share": 0.78,
                        "sourceEvidenceIds": ["PRIVATE-EVIDENCE"],
                    }
                ],
                "currentProductsAndServices": ["雲端整合"],
            },
            "customersAndChannels": {
                "customerConcentration": {
                    "period": "2025 FY",
                    "largestCustomerRevenueShare": 18.0,
                    "unit": "PERCENT",
                    "customerIdentity": "PRIVATE-CUSTOMER",
                    "sourceEvidenceIds": ["PRIVATE-EVIDENCE"],
                }
            },
            "financialPerformance": {
                "annualSnapshot": {
                    "period": "2025 FY",
                    "unit": "TWD_100_MILLION",
                    "revenue": 25.0,
                    "operatingIncome": 2.0,
                    "sourceEvidenceIds": ["PRIVATE-EVIDENCE"],
                }
            },
        },
        "frontendProjection": {
            "contractVersion": "company-research-frontend.v4",
            "researchGovernance": {
                "dataCompletenessScore": completeness,
                "confidenceLevel": "MEDIUM",
                "hasUnresolvedGaps": True,
                "publication": {
                    "publicationStatus": publication_status,
                    "ownerReviewStatus": owner_status,
                    "sourceRightsStatus": source_rights,
                    "blockingIssues": [],
                    "approvalEvidence": {
                        "decisionId": "PRIVATE-DECISION",
                        "reviewer": "owner",
                        "approvedAt": "2026-10-25T00:00:00Z",
                        "packageSha256": "",
                    }
                    if owner_status == "APPROVED"
                    else None,
                },
            },
            "investmentThemes": [
                {
                    "themeTitle": "企業雲端整合",
                    "timeHorizon": "近中期",
                    "opportunity": {
                        "summary": "專案交付帶動服務收入。",
                        "metrics": ["正式專案公告"],
                        "sourceEvidenceIds": ["PRIVATE-EVIDENCE"],
                    },
                }
            ],
            "operatingMatrix": [
                {
                    "id": "PRIVATE-BUSINESS-ID",
                    "name": "系統整合",
                    "products": [{"name": "雲端服務", "lifecycle": "COMMERCIAL_REVENUE"}],
                }
            ],
            "finance": {
                "forecast": {"forwardEps": None},
                "historicalTable": {
                    "rows": [
                        {
                            "metricKey": "revenue",
                            "label": "合併營收",
                            "values": {"current_q": 6.2},
                            "sourceEvidenceIds": ["PRIVATE-EVIDENCE"],
                        }
                    ]
                },
            },
        },
    }
    approval = result["frontendProjection"]["researchGovernance"]["publication"]["approvalEvidence"]
    if approval is not None:
        unsigned = json.loads(json.dumps(result, ensure_ascii=False))
        unsigned["frontendProjection"]["researchGovernance"]["publication"].pop("approvalEvidence")
        canonical = json.dumps(unsigned, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        approval["packageSha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return result


def test_public_projection_is_allowlisted_and_keeps_numeric_values(tmp_path) -> None:
    path = tmp_path / "research_package.json"
    path.write_text(json.dumps(package()), encoding="utf-8")

    result = FileCompanyProfileV4ReadStore(str(path)).get_public("2468")
    payload = result.model_dump(by_alias=True, mode="json")
    encoded = json.dumps(payload, ensure_ascii=False)

    assert payload["publicationStatus"] == "PUBLISHED"
    assert payload["overviewData"]["businessModel"]["shortDesc"] == "企業資訊系統整合與服務。"
    assert payload["sections"]["productsAndMarket"]["revenueMix"][0]["value"] == 21.0
    assert payload["sections"]["financialPerformance"]["annualSnapshot"]["revenue"] == 25.0
    assert (
        payload["sections"]["customersAndChannels"]["customerConcentration"][
            "largestCustomerRevenueShare"
        ]
        == 18.0
    )
    assert payload["operatingMatrix"][0]["products"][0]["lifecycle"] == "COMMERCIAL_REVENUE"
    assert payload["finance"]["forecast"]["forwardEps"] is None
    assert "PRIVATE-EVIDENCE" not in encoded
    assert "PRIVATE-DECISION" not in encoded
    assert "PRIVATE-BUSINESS-ID" not in encoded
    assert "PRIVATE-CUSTOMER" not in encoded
    assert "sourceEvidenceIds" not in encoded


def test_score_above_policy_threshold_publishes_without_claiming_owner_review(tmp_path) -> None:
    path = tmp_path / "research_package.json"
    path.write_text(json.dumps(package(owner_status="PENDING")), encoding="utf-8")

    result = FileCompanyProfileV4ReadStore(str(path)).get_public("2468")
    payload = result.model_dump(by_alias=True, mode="json")
    encoded = json.dumps(payload, ensure_ascii=False)

    assert result.publication_status == "PUBLISHED"
    assert result.overview_data["businessModel"]["shortDesc"] == "企業資訊系統整合與服務。"
    assert payload["researchGovernance"]["dataCompletenessScore"] == 0.72
    assert "OWNER_STANDING_POLICY" not in encoded
    assert "PRIVATE-EVIDENCE" not in encoded
    assert "authorizationEvidence" not in encoded


def test_completeness_threshold_is_strictly_greater_than_point_seven(tmp_path) -> None:
    path = tmp_path / "research_package.json"
    path.write_text(
        json.dumps(package(owner_status="PENDING", completeness=0.70)), encoding="utf-8"
    )

    result = FileCompanyProfileV4ReadStore(str(path)).get_public("2468")

    assert result.publication_status == "UNPUBLISHED"
    assert result.overview_data is None


def test_policy_does_not_bypass_source_rights_or_explicit_block(tmp_path) -> None:
    for source_rights, status in (("UNVERIFIED", "UNPUBLISHED"), ("BLOCKED", "BLOCKED")):
        path = tmp_path / f"{source_rights}.json"
        path.write_text(
            json.dumps(
                package(
                    owner_status="PENDING",
                    source_rights=source_rights,
                    publication_status="PUBLISHED" if source_rights == "UNVERIFIED" else "BLOCKED",
                )
            ),
            encoding="utf-8",
        )

        result = FileCompanyProfileV4ReadStore(str(path)).get_public("2468")

        assert result.publication_status == status
        assert result.overview_data is None


def test_content_changed_after_owner_hash_approval_is_blocked(tmp_path) -> None:
    approved = package()
    approved["overviewData"]["businessModel"]["shortDesc"] = "核准後被改寫的文字。"
    path = tmp_path / "research_package.json"
    path.write_text(json.dumps(approved), encoding="utf-8")

    result = FileCompanyProfileV4ReadStore(str(path)).get_public("2468")

    assert result.publication_status == "BLOCKED"
    assert result.overview_data is None


def test_missing_and_duplicate_packages_fail_closed(tmp_path) -> None:
    store = FileCompanyProfileV4ReadStore(str(tmp_path))
    assert store.get_public("2468").publication_status == "NOT_CONNECTED"

    (tmp_path / "first" / "research_package.json").parent.mkdir()
    (tmp_path / "first" / "research_package.json").write_text(
        json.dumps(package()), encoding="utf-8"
    )
    (tmp_path / "second" / "research_package.json").parent.mkdir()
    (tmp_path / "second" / "research_package.json").write_text(
        json.dumps(package()), encoding="utf-8"
    )
    assert store.get_public("2468").publication_status == "BLOCKED"


def test_read_endpoint_accepts_policy_publication_but_remains_get_only(tmp_path) -> None:
    path = tmp_path / "research_package.json"
    path.write_text(json.dumps(package(owner_status="PENDING")), encoding="utf-8")
    app = create_app(
        Settings(
            database_url="sqlite+pysqlite:///:memory:",
            company_profile_v4_read_model_path=str(path),
        )
    )

    response = TestClient(app).get("/api/v2/stocks/2468/research-v4")

    assert response.status_code == 200
    assert response.json()["publicationStatus"] == "PUBLISHED"
    assert response.json()["investmentThemes"]
    assert "authorizationEvidence" not in response.text
    assert not any(
        getattr(route, "path", "").endswith("/research-v4")
        and "POST" in getattr(route, "methods", set())
        for route in app.routes
    )


def test_database_read_store_returns_latest_public_projection_without_private_fields() -> None:
    payload = CompanyResearchV4PublicResponse(
        stockCode="2468",
        displayName="華經",
        publicationStatus="PUBLISHED",
        overviewData={"businessModel": {"shortDesc": "企業資訊系統整合與服務。"}},
    ).model_dump(by_alias=True, mode="json")
    session = _FakeSession(
        [
            _FakeResult(scalar=1),
            _FakeResult(row={"id": "instrument-2468", "is_active": True}),
            _FakeResult(row={"public_payload": payload}),
        ]
    )

    result = DatabaseCompanyProfileV4ReadStore(session).get_public("2468")

    assert result.publication_status == "PUBLISHED"
    assert result.overview_data["businessModel"]["shortDesc"] == "企業資訊系統整合與服務。"
    assert "evidenceId" not in result.model_dump_json()


def test_read_endpoint_uses_database_publication_when_file_store_is_unconfigured(
    monkeypatch,
) -> None:
    payload = CompanyResearchV4PublicResponse(
        stockCode="2468",
        displayName="華經",
        publicationStatus="PUBLISHED",
        overviewData={"businessModel": {"shortDesc": "企業資訊系統整合與服務。"}},
    ).model_dump(by_alias=True, mode="json")
    session = _FakeSession(
        [
            _FakeResult(scalar=1),
            _FakeResult(row={"id": "instrument-2468", "is_active": True}),
            _FakeResult(row={"public_payload": payload}),
        ]
    )
    from topicpilot_api.company_profile_v4 import api as research_api

    monkeypatch.setattr(
        research_api,
        "get_session_factory",
        lambda: lambda: nullcontext(session),
    )
    app = create_app(Settings(company_profile_v4_read_model_path=None))

    response = TestClient(app).get("/api/v2/stocks/2468/research-v4")

    assert response.status_code == 200
    assert response.json()["publicationStatus"] == "PUBLISHED"
    assert (
        response.json()["overviewData"]["businessModel"]["shortDesc"] == "企業資訊系統整合與服務。"
    )


def test_database_read_store_fails_closed_for_duplicate_master_identity() -> None:
    session = _FakeSession([_FakeResult(scalar=2)])

    result = DatabaseCompanyProfileV4ReadStore(session).get_public("2468")

    assert result.publication_status == "BLOCKED"
    assert result.overview_data is None


def test_database_read_store_returns_unpublished_state_when_publication_is_absent() -> None:
    session = _FakeSession(
        [
            _FakeResult(scalar=1),
            _FakeResult(row={"id": "instrument-2468", "is_active": True}),
            _FakeResult(row=None),
        ]
    )

    result = DatabaseCompanyProfileV4ReadStore(session).get_public("2468")

    assert result.publication_status == "NOT_CONNECTED"
    assert result.overview_data is None
