from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from topicpilot_api.bundle import BundleError, load_bundle
from topicpilot_api.config import get_settings
from topicpilot_api.importer import ImportConflictError, import_bundle


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate and import an enterprise_bundle.v1")
    parser.add_argument("bundle_dir", type=Path, help="Directory containing manifest.json")
    parser.add_argument("--schema", type=Path, help="Override the enterprise JSON Schema")
    parser.add_argument("--database-url", help="PostgreSQL SQLAlchemy URL")
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate and hash without writing to PostgreSQL",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        bundle = load_bundle(args.bundle_dir, args.schema)
        if args.validate_only:
            print(
                json.dumps(
                    {
                        "status": "VALID",
                        "bundleVersion": bundle.manifest["bundleVersion"],
                        "bundleHash": bundle.bundle_hash,
                        "rowCounts": bundle.row_counts,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0

        database_url = args.database_url or get_settings().database_url
        engine = create_engine(database_url, pool_pre_ping=True)
        with Session(engine) as session:
            result = import_bundle(session, bundle)
        print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
        return 0
    except (BundleError, ImportConflictError, OSError, ValueError) as exc:
        print(json.dumps({"status": "REJECTED", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
