"""Operator command for secret-free adapter-v2 provenance checks."""

from __future__ import annotations

import argparse
import json

from topicpilot_api.market_data.lineage import build_provider_lineage


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit JSON (the default output)")
    return parser


def main(argv: list[str] | None = None) -> int:
    build_parser().parse_args(argv)
    print(json.dumps(build_provider_lineage(), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
