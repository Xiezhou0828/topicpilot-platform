"""Build the Owner-authorized canonical Instrument expansion bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any

from topicpilot_api.reference_data.bootstrap import canonical_instrument_id
from topicpilot_api.reference_data.bundle import (
    ReferenceBundle,
    load_bundle,
    write_bundle,
)

TWSE_URL = "https://openapi.twse.com.tw/v1/opendata/t187ap03_L"
TPEX_URL = "https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_O"
TPEX_EMERGING_URL = "https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_R"
TPEX_6457_LISTING_URL = "https://www.tpex.org.tw/storage/eb_data/10406/10400146681.htm"
TPEX_6457_DELISTING_URL = (
    "https://dsp.tpex.org.tw/web/announcement/announcement_detail.php?"
    "content_file=MTEzMDAxMTA4NDEuaHRtbA%3D%3D&content_number=MTEzMDAxMTA4NDE%3D"
)
SOURCE_VERSION = "tw-reference-v1-rollover-57247b5a861c0ae3"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def iso_date(value: str) -> str:
    return date(int(value[:4]), int(value[4:6]), int(value[6:8])).isoformat()


def source_artifact(path: Path, role: str, url: str) -> dict[str, str]:
    return {"fileName": path.name, "role": role, "sha256": sha256(path), "sourceUrl": url}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", required=True, type=Path)
    parser.add_argument("--reconciliation", required=True, type=Path)
    parser.add_argument("--base-bundle", required=True, type=Path)
    parser.add_argument("--output-bundle", required=True, type=Path)
    parser.add_argument("--output-reconciliation", required=True, type=Path)
    parser.add_argument("--relation-artifact", required=True, type=Path)
    parser.add_argument("--output-relation-artifact", required=True, type=Path)
    args = parser.parse_args()

    files = {
        "twse": args.source_dir / "twse-listed-company-profile-20260912.json",
        "tpex": args.source_dir / "tpex-otc-company-profile-20260912.json",
        "emerging": args.source_dir / "tpex-emerging-company-profile-20260912.json",
        "listing6457": args.source_dir / "tpex-6457-listing-20150612.html",
        "delisting6457": args.source_dir / "tpex-6457-delisting-20250101.html",
    }
    twse = {row["公司代號"]: row for row in json.loads(files["twse"].read_text(encoding="utf-8-sig"))}
    tpex = {row["SecuritiesCompanyCode"]: row for row in json.loads(files["tpex"].read_text(encoding="utf-8-sig"))}
    emerging = {
        row["SecuritiesCompanyCode"]: row
        for row in json.loads(files["emerging"].read_text(encoding="utf-8-sig"))
    }
    unresolved = json.loads(args.reconciliation.read_text(encoding="utf-8"))["rows"]
    base = load_bundle(args.base_bundle)
    instruments = list(base.instruments)
    lifecycles = list(base.instrument_lifecycles)
    evidence: dict[str, Any] = json.loads(json.dumps(base.evidence))
    results = []

    for item in unresolved:
        market = item["marketCode"]
        code = item["instrumentCode"]
        own = twse.get(code) if market == "TPE" else tpex.get(code)
        opposite = tpex.get(code) if market == "TPE" else twse.get(code)
        if own is not None:
            name = own["公司簡稱"] if market == "TPE" else own["CompanyAbbreviation"].strip()
            listing = iso_date(own["上市日期"] if market == "TPE" else own["DateOfListing"])
            source_url = TWSE_URL if market == "TPE" else TPEX_URL
            status = "CANONICAL_APPROVED"
            reason = "CURRENT_OFFICIAL_EXCHANGE_PROFILE_EXACT_MARKET_CODE_MATCH"
            valid_to = None
        elif market == "TWO" and code == "6457":
            name = "紘康"
            listing = "2015-06-12"
            source_url = TPEX_6457_LISTING_URL
            status = "CANONICAL_APPROVED"
            reason = "OFFICIAL_TPEX_HISTORICAL_LISTING_AND_DELISTING_NOTICES"
            valid_to = "2025-01-01"
        else:
            status = "FORMALLY_EXCLUDED"
            listing = None
            valid_to = None
            if opposite is not None:
                actual_market = "TWO" if market == "TPE" else "TPE"
                name = (
                    opposite["CompanyAbbreviation"].strip()
                    if actual_market == "TWO"
                    else opposite["公司簡稱"]
                )
                source_url = TPEX_URL if actual_market == "TWO" else TWSE_URL
                reason = f"OFFICIAL_EXCHANGE_MARKET_MISMATCH:{market}->{actual_market}"
            elif market == "TPE" and code == "2644" and code in emerging:
                name = emerging[code]["CompanyAbbreviation"].strip()
                source_url = TPEX_EMERGING_URL
                reason = "OFFICIAL_TPEX_EMERGING_IDENTITY_NOT_TWSE_LISTED"
            else:
                raise SystemExit(f"unresolved official identity: {market}:{code}")

        result = {
            "marketCode": market,
            "instrumentCode": code,
            "name": name,
            "resolution": status,
            "reason": reason,
            "sourceReference": source_url,
            "listingEffectiveFrom": listing,
            "effectiveTo": valid_to,
            "canonicalUuidInput": (
                f"topicpilot.instrument.v1:{market}:{code}"
                if status == "CANONICAL_APPROVED"
                else None
            ),
            "canonicalUuid": (
                str(canonical_instrument_id(market, code))
                if status == "CANONICAL_APPROVED"
                else None
            ),
            "affectedRelationCount": item["affectedRelationCount"],
        }
        results.append(result)
        if status != "CANONICAL_APPROVED":
            continue
        instruments.append(
            {
                "market_code": market,
                "instrument_code": code,
                "name": name,
                "instrument_type": "EQUITY",
                "currency": "TWD",
                "valid_from": listing,
                "valid_to": valid_to,
                "is_active": valid_to is None,
            }
        )
        events = []
        if valid_to is not None:
            events.append(
                {
                    "market": market,
                    "status": "DELISTED",
                    "effectiveFrom": valid_to,
                    "evidenceId": "TPEX-TWO-6457-DELISTED-20250101",
                    "source": TPEX_6457_DELISTING_URL,
                    "reason": "TPEx official termination notice",
                }
            )
        if events:
            evidence.setdefault("suspensions", {})[code] = {
                "market": market,
                "events": events,
            }
        for event in events:
            lifecycles.append(
                {
                    "market_code": market,
                    "instrument_code": code,
                    "status_code": event["status"],
                    "effective_from": event["effectiveFrom"],
                    "evidence_id": event["evidenceId"],
                    "source_url": event["source"],
                    "reason": event["reason"],
                }
            )

    counts = {name: sum(row["resolution"] == name for row in results) for name in (
        "CANONICAL_APPROVED", "FORMALLY_EXCLUDED"
    )}
    if counts != {"CANONICAL_APPROVED": 49, "FORMALLY_EXCLUDED": 30}:
        raise SystemExit(f"unexpected reconciliation counts: {counts}")
    instruments.sort(key=lambda row: (row["market_code"], row["instrument_code"]))
    lifecycles.sort(key=lambda row: (
        row["market_code"], row["instrument_code"], row["effective_from"], row["status_code"]
    ))
    manifest = dict(base.manifest)
    manifest["referenceDataVersion"] = SOURCE_VERSION
    manifest["previousReferenceVersion"] = SOURCE_VERSION
    manifest["governance"] = {
        **manifest.get("governance", {}),
        "instrumentExpansion": "OWNER_APPROVED_CANONICAL_REFERENCE_EXPANSION_REVIEW_20260912",
        "instrumentIdentityUuid": "UUIDv5(topicpilot.instrument.v1:{marketCode}:{instrumentCode})",
        "dateEffectiveAuthority": "official TWSE/TPEx company profile or historical listing notice",
    }
    manifest["sourceArtifacts"] = list(manifest.get("sourceArtifacts", [])) + [
        source_artifact(files["twse"], "INSTRUMENT_EXPANSION_AUTHORITY", TWSE_URL),
        source_artifact(files["tpex"], "INSTRUMENT_EXPANSION_AUTHORITY", TPEX_URL),
        source_artifact(files["emerging"], "FORMAL_EXCLUSION_AUTHORITY", TPEX_EMERGING_URL),
        source_artifact(files["listing6457"], "HISTORICAL_LISTING_AUTHORITY", TPEX_6457_LISTING_URL),
        source_artifact(files["delisting6457"], "HISTORICAL_DELISTING_AUTHORITY", TPEX_6457_DELISTING_URL),
    ]
    bundle = ReferenceBundle(
        manifest=manifest,
        markets=base.markets,
        instruments=tuple(instruments),
        currencies=base.currencies,
        timezones=base.timezones,
        sessions=base.sessions,
        trading_statuses=base.trading_statuses,
        adjustments=base.adjustments,
        calendar_dates=base.calendar_dates,
        instrument_lifecycles=tuple(lifecycles),
        evidence=evidence,
    )
    manifest["derivedSummary"] = bundle.summary()
    write_bundle(bundle, args.output_bundle)
    result_payload = {
        "schemaVersion": "canonical-instrument-reconciliation.v1",
        "ownerDecision": "OWNER_APPROVES_CANONICAL_REFERENCE_EXPANSION_REVIEW",
        "referenceExpansionInput": len(results),
        "canonicalApproved": counts["CANONICAL_APPROVED"],
        "formallyExcluded": counts["FORMALLY_EXCLUDED"],
        "unresolved": 0,
        "rows": results,
    }
    result_payload["artifactSha256"] = hashlib.sha256(
        json.dumps(result_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    args.output_reconciliation.parent.mkdir(parents=True, exist_ok=True)
    args.output_reconciliation.write_text(
        json.dumps(result_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    relation = json.loads(args.relation_artifact.read_text(encoding="utf-8"))
    exclusions = {
        (row["marketCode"], row["instrumentCode"]): row
        for row in results
        if row["resolution"] == "FORMALLY_EXCLUDED"
    }
    excluded_rows = [
        row for row in relation["rows"]
        if (row["marketCode"], row["instrumentCode"]) in exclusions
    ]
    relation["rows"] = [
        row for row in relation["rows"]
        if (row["marketCode"], row["instrumentCode"]) not in exclusions
    ]
    if len(excluded_rows) != 56:
        raise SystemExit("formal relation exclusion count is not exact")
    previous_sha = relation["artifactSha256"]
    relation["authorityVersion"] = "structural-role-authority-20260912.v4"
    relation["approvalReference"] = "OWNER_APPROVES_CANONICAL_REFERENCE_EXPANSION_REVIEW_20260912"
    relation["expectedRelationCount"] = len(relation["rows"])
    relation["expectedExistingProductionCount"] = 440
    relation["expectedMissingProductionCount"] = len(relation["rows"]) - 440
    relation["instrumentReferenceAuthority"] = {
        "sourceReferenceVersion": SOURCE_VERSION,
        "expansionBundleSha256": bundle.digest(),
        "reconciliationSha256": result_payload["artifactSha256"],
        "canonicalApproved": counts["CANONICAL_APPROVED"],
        "formallyExcludedInstrumentIdentities": counts["FORMALLY_EXCLUDED"],
        "formallyExcludedRelationRows": len(excluded_rows),
    }
    relation["exclusionLineage"] = {
        "previousAuthorityVersion": "structural-role-authority-20260911.v3",
        "previousArtifactSha256": previous_sha,
        "reason": "OFFICIAL_MARKET_IDENTITY_MISMATCH_OR_NON_LISTED_MARKET_STATUS",
        "excludedRows": [
            {
                "marketCode": row["marketCode"],
                "instrumentCode": row["instrumentCode"],
                "topicId": row["topicId"],
                "relationId": row["relationId"],
                "evidence": exclusions[(row["marketCode"], row["instrumentCode"])],
            }
            for row in excluded_rows
        ],
    }
    relation.pop("artifactSha256")
    relation["artifactSha256"] = hashlib.sha256(
        json.dumps(relation, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    args.output_relation_artifact.parent.mkdir(parents=True, exist_ok=True)
    args.output_relation_artifact.write_text(
        json.dumps(relation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "bundleSha256": bundle.digest(),
        "canonicalApproved": counts["CANONICAL_APPROVED"],
        "formallyExcluded": counts["FORMALLY_EXCLUDED"],
        "reconciliationSha256": result_payload["artifactSha256"],
        "relationArtifactSha256": relation["artifactSha256"],
        "relationCount": len(relation["rows"]),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
