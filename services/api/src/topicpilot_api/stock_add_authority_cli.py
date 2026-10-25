"""Read only the live stock-master and Topic-catalog authority in CI."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import UTC, datetime
from typing import Any

from .stock_add_authority import (
    PROTECTED_DB_ROLE,
    FormalAuthorityReadError,
    FormalAuthoritySnapshot,
    read_protected_database_authority_snapshot,
)
from .stock_add_workflow import canonical_sha256


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Read the protected Production stock and Topic authorities; this command "
            "does not load a research package or perform writes."
        )
    )
    parser.add_argument("stock_code", help="Taiwan listed/OTC stock code")
    parser.add_argument("--market", choices=("TPE", "TWO"), required=True)
    parser.add_argument("--source-revision", required=True)
    return parser


def build_readback_report(
    *, stock_code: str, market: str, source_revision: str, snapshot: FormalAuthoritySnapshot
) -> dict[str, Any]:
    target_code = stock_code.strip()
    target_market = market.strip().upper()
    master = snapshot.master_evidence
    catalog = snapshot.topic_catalog_evidence
    body: dict[str, Any] = {
        "schemaVersion": "topicpilot-stock-add-authority-readback.v1",
        "mode": "PROTECTED_READ_ONLY_AUTHORITY_CHECK",
        "generatedAt": datetime.now(UTC).isoformat(timespec="seconds"),
        "producerRevision": source_revision.lower(),
        "identity": {"stockCode": target_code, "market": target_market},
        "stockMaster": {
            "status": snapshot.stock_status(target_code, target_market),
            "targetMatchCount": sum(
                str(item.get("code", "")).strip() == target_code
                and str(item.get("market", "")).strip().upper() == target_market
                for item in snapshot.stock_items
            ),
            "complete": master.complete,
            "readAt": master.read_at,
            "recordCount": master.record_count,
            "identitySha256": master.sha256,
            "scope": master.scope,
        },
        "topicCatalog": {
            "status": "READY" if catalog.complete else "RETRIEVAL_BLOCKED",
            "complete": catalog.complete,
            "readAt": catalog.read_at,
            "asOf": catalog.as_of,
            "recordCount": catalog.record_count,
            "identitySha256": catalog.sha256,
            "scope": catalog.scope,
        },
        "readControls": snapshot.read_controls,
        "productionMutation": False,
        "writesPerformed": [],
    }
    body["authorityReadbackSha256"] = canonical_sha256(body)
    return body


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if not re.fullmatch(r"[0-9]{4}(?:[0-9]{2})?", args.stock_code):
        print("INVALID_STOCK_CODE", file=sys.stderr)
        return 2
    if not re.fullmatch(r"[0-9a-fA-F]{40}", args.source_revision):
        print("SOURCE_REVISION_MUST_BE_EXACT_COMMIT_SHA", file=sys.stderr)
        return 2
    if os.environ.get("GITHUB_SHA", "").casefold() != args.source_revision.casefold():
        print("SOURCE_REVISION_MISMATCH_DISPATCHED_SHA", file=sys.stderr)
        return 2
    try:
        snapshot = read_protected_database_authority_snapshot(
            stock_code=args.stock_code,
            market=args.market,
        )
        if (
            not snapshot.master_evidence.verified_current_read
            or not snapshot.topic_catalog_evidence.verified_current_read
        ):
            raise FormalAuthorityReadError("PRODUCTION_CATALOG_READBACK_NOT_CURRENT")
        report = build_readback_report(
            stock_code=args.stock_code,
            market=args.market,
            source_revision=args.source_revision,
            snapshot=snapshot,
        )
    except FormalAuthorityReadError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    controls = report.get("readControls") or {}
    if (
        controls.get("databaseRole") != PROTECTED_DB_ROLE
        or controls.get("databaseTargetVerified") is not True
        or controls.get("transactionReadOnly") is not True
        or controls.get("transactionIsolation") != "repeatable read"
        or controls.get("mutationPrivilegesObserved") is not False
        or controls.get("temporaryDatabasePrivilegeObserved") is not False
        or controls.get("activeMarketCodes") != ["TPE", "TWO"]
        or not controls.get("migrationHead")
    ):
        print("PRODUCTION_CATALOG_READ_CONTROLS_INCOMPLETE", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
