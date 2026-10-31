"""Read only the live stock-master and Topic-catalog authority in CI."""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import unicodedata
from datetime import UTC, datetime
from typing import Any

from .stock_add_authority import (
    PROTECTED_DB_ROLE,
    FormalAuthorityReadError,
    FormalAuthoritySnapshot,
    read_protected_database_authority_snapshot,
)
from .stock_add_workflow import canonical_sha256

MAX_TOPIC_SEARCH_TERMS = 12
MAX_TOPIC_CANDIDATE_MATCHES = 20


def safe_github_summary_text(value: object) -> str:
    """Keep public catalog values as plain text in a GitHub Actions summary."""
    text = " ".join(str(value).split())
    text = html.escape(text, quote=False)
    for character, entity in {
        "`": "&#96;",
        "\\": "&#92;",
        "*": "&#42;",
        "_": "&#95;",
        "[": "&#91;",
        "]": "&#93;",
        "|": "&#124;",
        "~": "&#126;",
    }.items():
        text = text.replace(character, entity)
    return text


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
    parser.add_argument(
        "--topic-search-terms",
        default="[]",
        help="Optional JSON array of business terms; returns only bounded catalog name matches.",
    )
    return parser


def _validated_search_terms(raw: str) -> tuple[str, ...]:
    try:
        value = json.loads(raw)
    except (json.JSONDecodeError, TypeError) as exc:
        raise ValueError("TOPIC_SEARCH_TERMS_MUST_BE_JSON_ARRAY") from exc
    if not isinstance(value, list) or len(value) > MAX_TOPIC_SEARCH_TERMS:
        raise ValueError("TOPIC_SEARCH_TERMS_INVALID_COUNT")
    terms: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise ValueError("TOPIC_SEARCH_TERM_MUST_BE_STRING")
        term = " ".join(item.split()).strip()
        if (
            not term
            or not _normalize_match_text(term)
            or len(term) > 80
            or any(unicodedata.category(char) == "Cc" for char in term)
        ):
            raise ValueError("TOPIC_SEARCH_TERM_INVALID")
        if term.casefold() not in {existing.casefold() for existing in terms}:
            terms.append(term)
    return tuple(terms)


def _normalize_match_text(value: str) -> str:
    return "".join(
        char.casefold() for char in unicodedata.normalize("NFKC", value) if char.isalnum()
    )


def _topic_name_candidates(
    snapshot: FormalAuthoritySnapshot, terms: tuple[str, ...]
) -> dict[str, Any]:
    if not terms:
        return {"status": "NOT_REQUESTED", "searchTerms": [], "matches": []}

    normalized_terms = {term: _normalize_match_text(term) for term in terms}
    matches: list[dict[str, Any]] = []
    for topic in snapshot.topic_items:
        if topic.get("enabled") is not True:
            continue
        name = topic.get("name")
        slug = topic.get("slug")
        if not isinstance(name, str) or not isinstance(slug, str):
            continue
        searchable = _normalize_match_text(f"{name} {slug}")
        matched_terms = [
            term for term, normalized in normalized_terms.items() if normalized in searchable
        ]
        if not matched_terms:
            continue
        hierarchy = topic.get("hierarchy")
        parents = hierarchy.get("parents", []) if isinstance(hierarchy, dict) else []
        parent_names = sorted(
            {
                str(parent.get("name")).strip()
                for parent in parents
                if isinstance(parent, dict) and isinstance(parent.get("name"), str)
            }
        )
        matches.append(
            {
                "slug": slug,
                "name": name,
                "status": topic.get("status"),
                "parentNames": parent_names,
                "matchedTerms": matched_terms,
                "decisionStatus": "NAME_MATCH_REQUIRES_EVIDENCE_REVIEW",
            }
        )

    matches.sort(key=lambda row: (str(row["slug"]), str(row["name"])))
    if len(matches) > MAX_TOPIC_CANDIDATE_MATCHES:
        return {
            "status": "TOO_BROAD",
            "searchTerms": list(terms),
            "matches": [],
            "matchCount": len(matches),
            "maximumMatches": MAX_TOPIC_CANDIDATE_MATCHES,
        }
    return {
        "status": "MATCHES_RETURNED" if matches else "NO_NAME_MATCH",
        "searchTerms": list(terms),
        "matches": matches,
        "matchCount": len(matches),
        "maximumMatches": MAX_TOPIC_CANDIDATE_MATCHES,
    }


def build_readback_report(
    *,
    stock_code: str,
    market: str,
    source_revision: str,
    snapshot: FormalAuthoritySnapshot,
    topic_search_terms: tuple[str, ...] = (),
) -> dict[str, Any]:
    topic_search_terms = _validated_search_terms(json.dumps(list(topic_search_terms)))
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
        "topicNameCandidateReadback": _topic_name_candidates(snapshot, topic_search_terms),
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
        topic_search_terms = _validated_search_terms(args.topic_search_terms)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
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
            topic_search_terms=topic_search_terms,
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
        or controls.get("directDatabaseMutationPrivilegeObserved") is not False
        or controls.get("activeMarketCodes") != ["TPE", "TWO"]
        or not controls.get("migrationHead")
    ):
        print("PRODUCTION_CATALOG_READ_CONTROLS_INCOMPLETE", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
