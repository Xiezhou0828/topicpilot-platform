from __future__ import annotations

import argparse
import json
import re
from typing import Any

MIGRATION_NUMBER = re.compile(r"^(?P<number>[0-9]{4})")


def migration_identity(value: str) -> tuple[int, str]:
    match = MIGRATION_NUMBER.match(value)
    if not match:
        raise ValueError(f"invalid migration head: {value}")
    return int(match.group("number")), value


def evaluate_migration_lineage(candidate: str, production: str) -> dict[str, Any]:
    candidate_number, candidate_identity = migration_identity(candidate)
    production_number, production_identity = migration_identity(production)
    if production_number > candidate_number:
        return {
            "status": "BLOCKED_MIGRATION",
            "reason": "production migration is newer than candidate; downgrade is forbidden",
            "candidate": candidate_identity,
            "production": production_identity,
        }
    if production_number == candidate_number and production_identity != candidate_identity:
        return {
            "status": "BLOCKED_MIGRATION_LINEAGE",
            "reason": "candidate and Production migration lineages differ at the same revision",
            "candidate": candidate_identity,
            "production": production_identity,
        }
    return {
        "status": "MIGRATION_COMPATIBLE",
        "reason": "candidate migration is not older than Production and lineage matches",
        "candidate": candidate_identity,
        "production": production_identity,
    }


def evaluate_release(
    *,
    candidate_migration: str,
    production_migration: str,
    expected_shas: dict[str, str | None] | None = None,
    observed_shas: dict[str, str | None] | None = None,
) -> dict[str, Any]:
    migration = evaluate_migration_lineage(candidate_migration, production_migration)
    mismatches: list[str] = []
    expected_shas = expected_shas or {}
    observed_shas = observed_shas or {}
    for surface, expected in expected_shas.items():
        observed = observed_shas.get(surface)
        if not expected or not observed:
            mismatches.append(f"{surface} exact SHA unavailable")
        elif expected != observed:
            mismatches.append(f"{surface} exact SHA mismatch: expected {expected}, observed {observed}")

    if migration["status"] != "MIGRATION_COMPATIBLE":
        status = migration["status"]
    elif mismatches:
        status = "BLOCKED_PROVENANCE"
    else:
        status = "READY"
    return {
        "status": status,
        "migration": migration,
        "provenance_gaps": mismatches,
        "production_mutation": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the fail-closed release gate.")
    parser.add_argument("--candidate-migration", required=True)
    parser.add_argument("--production-migration", required=True)
    parser.add_argument("--expected-api-sha")
    parser.add_argument("--api-sha")
    parser.add_argument("--expected-web-sha")
    parser.add_argument("--web-sha")
    parser.add_argument("--expected-worker-sha")
    parser.add_argument("--worker-sha")
    args = parser.parse_args()
    result = evaluate_release(
        candidate_migration=args.candidate_migration,
        production_migration=args.production_migration,
        expected_shas={
            "api": args.expected_api_sha,
            "web": args.expected_web_sha,
            "worker": args.expected_worker_sha,
        },
        observed_shas={
            "api": args.api_sha,
            "web": args.web_sha,
            "worker": args.worker_sha,
        },
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "READY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
