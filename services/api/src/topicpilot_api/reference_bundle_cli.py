"""Offline generation and validation command for canonical reference bundles."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from topicpilot_api.reference_data import (
    BundleValidationError,
    build_bundle_from_sources,
    load_bundle,
    write_bundle,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    generate = commands.add_parser(
        "generate", help="generate a canonical bundle from approved inputs"
    )
    generate.add_argument("--stock-source", type=Path, required=True)
    generate.add_argument("--calendar-source", type=Path, required=True)
    generate.add_argument("--evidence-source", type=Path, required=True)
    generate.add_argument(
        "--adjustment-source",
        type=Path,
        default=Path(__file__).with_name("reference_data")
        / "governance"
        / "adjustment_catalogue.json",
    )
    generate.add_argument("--reference-version", default="tw-reference-v1")
    generate.add_argument("--output-dir", type=Path, required=True)
    validate = commands.add_parser("validate", help="validate an existing canonical bundle")
    validate.add_argument("--bundle-dir", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "generate":
            bundle = build_bundle_from_sources(
                stock_source=args.stock_source,
                calendar_source=args.calendar_source,
                evidence_source=args.evidence_source,
                adjustment_source=args.adjustment_source,
                version=args.reference_version,
            )
            output_dir = write_bundle(bundle, args.output_dir)
            output = {"operation": "GENERATED", "bundleDir": str(output_dir), **bundle.summary()}
        else:
            bundle = load_bundle(args.bundle_dir)
            output = {
                "operation": "VALIDATED",
                "bundleDir": str(args.bundle_dir),
                **bundle.summary(),
            }
    except BundleValidationError as exc:
        print(json.dumps({"status": "BLOCKED", "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(output, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
