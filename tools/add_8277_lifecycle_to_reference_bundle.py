"""Add the official TPEx 8277 date-effective suspension to a reference bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from topicpilot_api.reference_data.bundle import (
    ReferenceBundle,
    load_bundle,
    write_bundle,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--authority", required=True, type=Path)
    args = parser.parse_args()

    bundle = load_bundle(args.bundle)
    authority = json.loads(args.authority.read_text(encoding="utf-8"))
    event = authority["events"][0]
    key = (authority["marketCode"], authority["instrumentCode"])
    if key not in {
        (row["market_code"], row["instrument_code"]) for row in bundle.instruments
    }:
        raise SystemExit("8277 canonical instrument identity is missing")

    lifecycles = [
        row
        for row in bundle.instrument_lifecycles
        if row.get("evidence_id") != event["evidenceId"]
    ]
    lifecycles.append(
        {
            "market_code": key[0],
            "instrument_code": key[1],
            "status_code": event["status"],
            "effective_from": event["effectiveFrom"],
            "effective_to": event["effectiveTo"],
            "evidence_id": event["evidenceId"],
            "source_url": authority["authority"]["endpoint"],
            "reason": event["reason"],
        }
    )
    lifecycles.sort(
        key=lambda row: (
            row["market_code"],
            row["instrument_code"],
            row["effective_from"],
            row["status_code"],
        )
    )

    evidence = json.loads(json.dumps(bundle.evidence))
    evidence.setdefault("suspensions", {})[key[1]] = {
        "market": key[0],
        "events": [
            {
                "market": key[0],
                "status": event["status"],
                "effectiveFrom": event["effectiveFrom"],
                "effectiveTo": event["effectiveTo"],
                "evidenceId": event["evidenceId"],
                "source": authority["authority"]["endpoint"],
                "sourceDocument": authority["subject"],
                "sourceNoticeNumber": authority["noticeNumber"],
                "sourceNoticeDate": authority["noticeDate"],
                "oldShareLastTradingDate": event["oldShareLastTradingDate"],
                "newShareBaseDate": event["newShareBaseDate"],
                "newShareTradingDate": event["newShareTradingDate"],
                "reason": event["reason"],
            }
        ],
    }

    manifest = dict(bundle.manifest)
    manifest["governance"] = {
        **manifest.get("governance", {}),
        "instrument8277Lifecycle": "OFFICIAL_TPEX_BULLETIN_11500055041",
    }
    source_artifacts = [
        row
        for row in manifest.get("sourceArtifacts", [])
        if row.get("fileName") != args.authority.name
    ]
    source_artifacts.append(
        {
            "fileName": args.authority.name,
            "role": "STATUS_EVIDENCE_ADDENDUM",
            "sha256": hashlib.sha256(args.authority.read_bytes()).hexdigest(),
            "sourceUrl": authority["authority"]["endpoint"],
            "documentDate": authority["noticeDate"],
            "sourceDescription": "TPEx official 8277 capital-reduction share-exchange notice",
        }
    )
    manifest["sourceArtifacts"] = source_artifacts
    updated = ReferenceBundle(
        manifest=manifest,
        markets=bundle.markets,
        instruments=bundle.instruments,
        currencies=bundle.currencies,
        timezones=bundle.timezones,
        sessions=bundle.sessions,
        trading_statuses=bundle.trading_statuses,
        adjustments=bundle.adjustments,
        calendar_dates=bundle.calendar_dates,
        instrument_lifecycles=tuple(lifecycles),
        evidence=evidence,
    )
    manifest["derivedSummary"] = updated.summary()
    write_bundle(updated, args.bundle)
    print(json.dumps({"bundleSha256": updated.digest(), "summary": updated.summary()}))


if __name__ == "__main__":
    main()
