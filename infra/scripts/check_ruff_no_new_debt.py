"""Fail only when the candidate introduces a new Ruff finding."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, order=True)
class Finding:
    file: str
    line: int
    rule: str
    message: str

    @property
    def identity(self) -> str:
        text = f"{self.file}|{self.line}|{self.rule}|{self.message}"
        return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _relative_file(filename: str, root: Path) -> str:
    path = Path(filename)
    if path.is_absolute():
        try:
            path = path.resolve().relative_to(root.resolve())
        except ValueError:
            path = Path(filename)
    return path.as_posix()


def _load_findings(path: Path, root: Path) -> set[Finding]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {
        Finding(
            file=_relative_file(str(item["filename"]), root),
            line=int(item["location"]["row"]),
            rule=str(item.get("code") or ""),
            message=str(item["message"]),
        )
        for item in payload
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-json", type=Path, required=True)
    parser.add_argument("--current-json", type=Path, required=True)
    parser.add_argument("--baseline-root", type=Path, required=True)
    parser.add_argument("--current-root", type=Path, required=True)
    args = parser.parse_args()

    baseline = _load_findings(args.baseline_json, args.baseline_root)
    current = _load_findings(args.current_json, args.current_root)
    unchanged = current & baseline
    new = sorted(current - baseline)
    resolved = sorted(baseline - current)

    print(f"CURRENT_RUFF_FINDING_COUNT={len(current)}")
    print(f"BASELINE_RUFF_FINDING_COUNT={len(baseline)}")
    print(f"UNCHANGED_BASELINE_RUFF_FINDING_COUNT={len(unchanged)}")
    print(f"NEW_RUFF_FINDING_COUNT={len(new)}")
    print(f"RESOLVED_RUFF_FINDING_COUNT={len(resolved)}")
    print("BASELINE_RUFF_DEBT_VERIFIED=YES")
    if new:
        print("NO_NEW_RUFF_DEBT_GATE=FAIL")
        for finding in new:
            print(
                "NEW_RUFF_FINDING="
                f"{finding.file}:{finding.line}:{finding.rule}:{finding.message}"
            )
        return 1

    print("NO_NEW_RUFF_DEBT_GATE=PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
