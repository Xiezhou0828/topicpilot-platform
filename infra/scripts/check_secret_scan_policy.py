"""Regression checks for the narrowly scoped Gitleaks revision allowlist."""

from __future__ import annotations

import re
from pathlib import Path

import tomllib

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / ".gitleaks.toml"
REVISION_SHA = "0123456789abcdef0123456789abcdef01234567"


def main() -> None:
    config = tomllib.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    assert config["extend"]["useDefault"] is True
    allowlist = config["allowlist"]
    assert allowlist["regexTarget"] == "match"
    assert len(allowlist["regexes"]) == 1
    revision_pattern = re.compile(allowlist["regexes"][0])

    allowed = [
        f"{key}={REVISION_SHA}"
        for key in (
            "API_REVISION",
            "WORKER_REVISION",
            "WEB_REVISION",
            "CANONICAL_SHA",
            "CANDIDATE_SHA",
            "RELEASED_SHA",
            "PROMOTED_CANONICAL_SHA",
        )
    ]
    rejected = [
        "API_" + "TOKEN=" + REVISION_SHA,
        "SECRET_" + "KEY=" + REVISION_SHA,
        f"API_REVISION={REVISION_SHA[:-1]}",
        f"API_REVISION={REVISION_SHA}0",
        f"API_REVISION={REVISION_SHA[:-1]}-",
        "PASSWORD=" + "dGhpcy1pcy1ub3QtYS1zZWNyZXQta2V5",
    ]

    assert all(revision_pattern.fullmatch(value) for value in allowed)
    assert all(not revision_pattern.fullmatch(value) for value in rejected)
    print("SECRET_SCAN_POLICY_STATUS=PASS")
    print("REVISION_METADATA_ALLOWED=YES")
    print("TRUE_POSITIVE_SECRET_CASES_STILL_REJECTED=YES")


if __name__ == "__main__":
    main()
