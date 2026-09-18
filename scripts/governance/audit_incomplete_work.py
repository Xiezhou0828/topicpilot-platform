from __future__ import annotations

import argparse
import json
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from _lib import REPO_ROOT

MARKERS: tuple[tuple[str, str], ...] = (
    ("TODO", "INCOMPLETE_CANDIDATE"),
    ("FIXME", "INCOMPLETE_CANDIDATE"),
    ("HACK", "INCOMPLETE_CANDIDATE"),
    ("XXX", "INCOMPLETE_CANDIDATE"),
    ("NotImplemented", "INCOMPLETE_CANDIDATE"),
    ("placeholder", "PLACEHOLDER_CANDIDATE"),
    ("fixture", "FIXTURE_OR_SYNTHETIC_CANDIDATE"),
    ("synthetic", "FIXTURE_OR_SYNTHETIC_CANDIDATE"),
    ("mock", "FIXTURE_OR_SYNTHETIC_CANDIDATE"),
    ("legacy", "LEGACY_OR_DEPRECATED_CANDIDATE"),
    ("deprecated", "LEGACY_OR_DEPRECATED_CANDIDATE"),
    ("orphan", "ORPHAN_CANDIDATE"),
    ("unwired", "ORPHAN_CANDIDATE"),
    ("dead", "ORPHAN_CANDIDATE"),
)


def scan_text(text: str, path: str) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        lowered = line.lower()
        for marker, classification in MARKERS:
            pattern = re.escape(marker.lower())
            if re.search(rf"(?<![a-z0-9_]){pattern}(?![a-z0-9_])", lowered):
                hits.append(
                    {
                        "path": path.replace("\\", "/"),
                        "line": line_number,
                        "marker": marker,
                        "classification": classification,
                    }
                )
    return hits


def iter_files(root: Path) -> Iterable[Path]:
    excluded = {".git", "node_modules", "dist", "build", ".venv", "__pycache__"}
    for path in root.rglob("*"):
        if path.is_file() and not any(part in excluded for part in path.parts):
            yield path


def scan_tree(root: Path, max_hits: int | None = None) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for path in iter_files(root):
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        hits.extend(scan_text(text, str(path.relative_to(root))))
        if max_hits and len(hits) >= max_hits:
            return hits[:max_hits]
    return hits


def main() -> int:
    parser = argparse.ArgumentParser(description="Detect incomplete-work candidates without changing files.")
    parser.add_argument("--path", type=Path, default=REPO_ROOT)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--max-hits", type=int, default=2000)
    args = parser.parse_args()
    root = args.path.resolve()
    hits = scan_tree(root, max_hits=args.max_hits)
    if args.summary:
        by_class: dict[str, int] = {}
        for hit in hits:
            by_class[hit["classification"]] = by_class.get(hit["classification"], 0) + 1
        print(json.dumps({"root": str(root), "hits": len(hits), "by_class": by_class}, sort_keys=True))
    elif args.json:
        print(json.dumps(hits, ensure_ascii=False, indent=2))
    else:
        for hit in hits:
            print(
                f"{hit['path']}:{hit['line']}: {hit['marker']} "
                f"[{hit['classification']}]"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
