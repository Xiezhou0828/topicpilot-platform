"""Validate FastAPI OpenAPI output and optionally compare it with a baseline."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import Any

REQUIRED_PATHS = {
    "/healthz",
    "/readyz",
    "/api/v1/meta/data-status",
    "/api/v1/snapshot/latest",
    "/api/v1/stocks",
    "/api/v1/topics",
    "/api/v1/strategies",
    "/api/v1/analytics/topic-rotation",
    "/api/v1/analytics/strategy-performance",
}


def load_app(reference: str) -> Any:
    module_name, separator, attribute = reference.partition(":")
    if not separator:
        raise ValueError("ASGI app must use module:attribute syntax")
    module = importlib.import_module(module_name)
    return getattr(module, attribute)


def normalize(document: dict[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(document, sort_keys=True, separators=(",", ":")))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--app", default="topicpilot_api.main:app")
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--write", type=Path)
    args = parser.parse_args()

    document = normalize(load_app(args.app).openapi())
    if not str(document.get("openapi", "")).startswith("3."):
        print("OpenAPI output is missing a supported 3.x version", file=sys.stderr)
        return 1

    missing = sorted(REQUIRED_PATHS - set(document.get("paths", {})))
    if missing:
        print(
            f"OpenAPI output is missing required paths: {', '.join(missing)}",
            file=sys.stderr,
        )
        return 1

    if args.write:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(
            json.dumps(document, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    if args.baseline:
        if not args.baseline.exists():
            print(
                f"::notice::No OpenAPI baseline at {args.baseline}; schema shape was validated only."
            )
            return 0
        baseline = normalize(json.loads(args.baseline.read_text(encoding="utf-8")))
        if document != baseline:
            print(
                "OpenAPI drift detected. Regenerate the committed client/schema intentionally.",
                file=sys.stderr,
            )
            return 1

    print("OpenAPI schema is valid and contains the required read-only routes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
