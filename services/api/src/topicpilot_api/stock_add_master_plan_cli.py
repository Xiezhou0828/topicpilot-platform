"""Seal a reviewed stock-add master plan with its deterministic final hash."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from topicpilot_api.company_profile_v4.store import prepare_research_publication
from topicpilot_api.stock_add_master_writer import (
    StockAddWriterError,
    canonical_sha256,
    expected_confirmation,
    validate_master_plan,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan_file", help="Reviewed JSON plan without planSha256")
    parser.add_argument("--output", help="Output file; defaults to standard output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        payload = json.loads(Path(args.plan_file).read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or "planSha256" in payload:
            raise StockAddWriterError("PLAN_INPUT_MUST_BE_OBJECT_WITHOUT_PLAN_SHA256")
        prepared_package = prepare_research_publication(payload.get("researchPackage"))
        if prepared_package is None:
            raise StockAddWriterError("RESEARCH_PACKAGE_NOT_PUBLICATION_AUTHORIZED")
        payload["researchPackage"] = prepared_package
        plan = {**payload, "planSha256": canonical_sha256(payload)}
        _, digest, _ = validate_master_plan(plan)
        confirmation = expected_confirmation(
            plan["stock"]["market"], plan["stock"]["stockCode"], digest
        )
        rendered = json.dumps(plan, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        if args.output:
            Path(args.output).write_text(rendered, encoding="utf-8")
        else:
            sys.stdout.write(rendered)
        print(f"FINAL_CONFIRMATION={confirmation}", file=sys.stderr)
        return 0
    except (OSError, json.JSONDecodeError, StockAddWriterError) as exc:
        error = json.dumps({"status": "BLOCKED", "reason": str(exc)}, ensure_ascii=False)
        print(error, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
