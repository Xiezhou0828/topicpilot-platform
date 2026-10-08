"""Fail-closed checks for revision and exact replay source-digest exceptions."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

import tomllib

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / ".gitleaks.toml"
REVISION_SHA = "0123456789abcdef0123456789abcdef01234567"
REVISION_PATTERN = (
    r"^(API_REVISION|WORKER_REVISION|WEB_REVISION|CANONICAL_SHA|CANDIDATE_SHA|"
    r"RELEASED_SHA|PROMOTED_CANONICAL_SHA)=[0-9a-fA-F]{40}\r?$"
)
REPORT_COMMIT = "524739323befc2c3abcb0b48dbbc42b7ff54daf1"
REPORT_DIRECTORY = (
    "docs/reports/TASK-20261002-TARGET-UNIVERSE-REPLAY-AND-READINESS-GATE-RESOLUTION"
)
FORMAL_CLOSURE_REPORT = (
    "docs/reports/"
    "TASK-FORMAL-STRENGTH-LIFECYCLE-20261007-FAIL-CLOSED-ROOT-CAUSE-AND-NATURAL-PUBLICATION-004.md"
)
PRODUCTION_RUNTIME_COMMIT = "646deea23ebfd7afb415201d0f9b2f11ab6fd099"
REPORT_SOURCES = {
    "baseline-replay-price-free.json": "3f2d4761c665931708517f0501c57f2be257b641",
    "candidate-replay-price-free.json": REPORT_COMMIT,
}
APPROVED_MODULES = ("topicpilot_api.market_data.history", "topicpilot_api.daily_market")


def git_blob(revision: str, path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{revision}:{path}"], cwd=ROOT)


def approved_metadata() -> list[tuple[str, str, str]]:
    """Recompute the four digests; historical report claims are not authority."""
    approved = []
    for filename, source_revision in REPORT_SOURCES.items():
        path = f"{REPORT_DIRECTORY}/{filename}"
        report = json.loads(git_blob(REPORT_COMMIT, path))
        for module in APPROVED_MODULES:
            source_path = f"services/api/src/{module.replace('.', '/')}.py"
            digest = hashlib.sha256(git_blob(source_revision, source_path)).hexdigest()
            assert report["implementationSourceSha256"][module] == digest
            approved.append((path, module, digest))
    return approved


def metadata_match(field: str, value: str) -> str:
    # The inherited detector's match excludes the JSON key's opening quote.
    return f"{field}\": {json.dumps(value)}"


def source_metadata_allowed(allowlists: list[dict], path: str, match: str) -> bool:
    return any(
        any(re.fullmatch(pattern, path) for pattern in entry["paths"])
        and any(re.fullmatch(pattern, match) for pattern in entry["regexes"])
        for entry in allowlists
    )


def metadata_cases(approved: list[tuple[str, str, str]]) -> list[tuple[str, str, str, bool]]:
    cases = [
        (f"approved_{number}", path, metadata_match(field, digest), True)
        for number, (path, field, digest) in enumerate(approved)
    ]
    path, field, digest = approved[0]
    line = metadata_match(field, digest)
    other_digest = hashlib.sha256(b"non-credential negative regression fixture").hexdigest()
    rejected = [
        ("wrong_path", "docs/reports/unapproved-replay.json", line),
        ("path_suffix", path + ".bak", line),
        ("path_prefix", "unapproved/" + path, line),
        ("cross_report_value", approved[2][0], line),
        ("wrong_source_value", path, metadata_match(field, other_digest)),
        ("wrong_module", path, metadata_match(APPROVED_MODULES[1], digest)),
        ("wrong_field_case", path, metadata_match(field.upper(), digest)),
        ("api_token", path, metadata_match("API_" + "TOKEN", digest)),
        ("api_key", path, metadata_match("api" + "Key", digest)),
        ("password", path, metadata_match("pass" + "word", digest)),
        ("secret_key", path, metadata_match("SECRET_" + "KEY", digest)),
        ("credential_same_line", path, line + metadata_match("api_" + "token", other_digest)),
        ("credential_next_line", path, line + "\n" + metadata_match("api_" + "token", other_digest)),
        ("non_hex_value", path, metadata_match(field, "ghp_" + other_digest[:36])),
    ]
    return cases + [(name, filename, value, False) for name, filename, value in rejected]


def check_native_gitleaks(executable: Path, cases: list[tuple[str, str, str, bool]]) -> None:
    """Exercise the real detector on controlled, non-credential negative fixtures."""
    artifact_root = ROOT / "work"
    artifact_root.mkdir(exist_ok=True)
    for name, path, line, expected_allowed in cases:
        with tempfile.TemporaryDirectory(prefix="secret-policy-", dir=artifact_root) as temporary:
            temporary_root = Path(temporary)
            source = temporary_root / "source"
            fixture = source / path
            fixture.parent.mkdir(parents=True)
            fixture.write_text(line + "\n", encoding="utf-8")
            report_path = temporary_root / "redacted-findings.json"
            result = subprocess.run(
                [
                    str(executable), "dir", ".", "--config", str(CONFIG_PATH),
                    "--redact", "--no-banner", "--no-color", "--exit-code", "2",
                    "--report-format", "json", "--report-path", str(report_path),
                ],
                cwd=source,
                capture_output=True,
                text=True,
                check=False,
            )
            findings = json.loads(report_path.read_text(encoding="utf-8"))
            assert result.returncode == (0 if expected_allowed else 2), name
            assert (len(findings) == 0) == expected_allowed, name
    print(f"NATIVE_GITLEAKS_REGRESSION_CASES_PASSED={len(cases)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gitleaks-executable", type=Path)
    args = parser.parse_args()
    config = tomllib.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    assert config["extend"] == {"useDefault": True}
    allowlist = config["allowlist"]
    assert set(allowlist) == {"description", "regexTarget", "regexes"}
    assert allowlist["regexTarget"] == "match"
    assert allowlist["regexes"] == [REVISION_PATTERN]  # Existing global policy is frozen.
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
        "API_REVISION=" + hashlib.sha256(b"unapproved revision length").hexdigest(),
        "PASSWORD=" + "dGhpcy1pcy1ub3QtYS1zZWNyZXQta2V5",
    ]

    assert all(revision_pattern.fullmatch(value) for value in allowed)
    assert all(not revision_pattern.fullmatch(value) for value in rejected)

    assert len(config["rules"]) == 1
    rule = config["rules"][0]
    assert set(rule) == {"id", "allowlists"}
    assert rule["id"] == "generic-api-key"  # No default detector attributes replaced.
    allowlists = rule["allowlists"]
    assert len(allowlists) == 3
    production_entry = allowlists[0]
    assert set(production_entry) == {
        "description",
        "condition",
        "regexTarget",
        "paths",
        "regexes",
    }
    assert production_entry["condition"] == "AND"
    assert production_entry["regexTarget"] == "match"
    assert production_entry["paths"] == [
        "^" + FORMAL_CLOSURE_REPORT.replace(".", r"\.") + "$"
    ]
    assert production_entry["regexes"] == [
        rf"^PRODUCTION_API_SHA={PRODUCTION_RUNTIME_COMMIT}$",
        rf"^PRODUCTION_API_RUNTIME_COMMIT={PRODUCTION_RUNTIME_COMMIT}$",
    ]
    approved = approved_metadata()
    for entry, filename in zip(allowlists[1:], REPORT_SOURCES, strict=True):
        assert set(entry) == {"description", "condition", "regexTarget", "paths", "regexes"}
        assert entry["condition"] == "AND"
        assert entry["regexTarget"] == "match"
        expected_path = f"{REPORT_DIRECTORY}/{filename}"
        assert entry["paths"] == ["^" + expected_path.replace(".", r"\.") + "$"]
        expected_patterns = [
            rf'^{re.escape(field)}":[ \t]*"{digest}"$'
            for path, field, digest in approved if path == expected_path
        ]
        assert entry["regexes"] == expected_patterns

    cases = metadata_cases(approved)
    for name, path, line, expected in cases:
        assert source_metadata_allowed(allowlists, path, line) == expected, name
    if args.gitleaks_executable:
        check_native_gitleaks(args.gitleaks_executable.resolve(), cases)
    print("SECRET_SCAN_POLICY_STATUS=PASS")
    print("REVISION_METADATA_ALLOWED=YES")
    print("APPROVED_SOURCE_SHA256_VERIFIED=4")
    print(f"SOURCE_METADATA_REGRESSION_CASES_PASSED={len(cases)}")
    print("TRUE_POSITIVE_SECRET_CASES_STILL_REJECTED=YES")


if __name__ == "__main__":
    main()
