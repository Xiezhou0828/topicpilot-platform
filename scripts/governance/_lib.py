from __future__ import annotations

import json
import subprocess
from collections.abc import Iterable
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE_ROOT = REPO_ROOT / "docs" / "governance"
TASKS_ROOT = GOVERNANCE_ROOT / "tasks"


def normalize_path(value: str | Path) -> str:
    text = str(value).replace("\\", "/")
    while text.startswith("./"):
        text = text[2:]
    return text.rstrip("/") if text != "/" else text


def load_json_compatible_yaml(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path} must be valid JSON-compatible YAML: {exc}") from exc


def git_output(*args: str, cwd: Path = REPO_ROOT) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def git_commit_exists(commit: str, cwd: Path = REPO_ROOT) -> bool:
    if not commit or any(char in commit for char in " \t\r\n"):
        return False
    result = subprocess.run(
        ["git", "cat-file", "-e", f"{commit}^{{commit}}"],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


def path_matches(path: str, pattern: str) -> bool:
    """Match bounded repository globs without treating a prefix as ownership."""
    candidate = normalize_path(path)
    rule = normalize_path(pattern)
    if rule.endswith("/**"):
        prefix = rule[:-3].rstrip("/")
        return candidate == prefix or candidate.startswith(prefix + "/")
    if rule.endswith("/"):
        return candidate.startswith(rule)
    import fnmatch

    return fnmatch.fnmatchcase(candidate, rule)


def any_path_matches(path: str, patterns: Iterable[str]) -> bool:
    return any(path_matches(path, pattern) for pattern in patterns)


def manifest_paths(manifest: dict[str, Any], key: str) -> list[str]:
    value = manifest.get(key, [])
    return [str(item) for item in value] if isinstance(value, list) else []


def load_manifest(path: Path) -> dict[str, Any]:
    value = load_json_compatible_yaml(path)
    if not isinstance(value, dict):
        raise TypeError(f"{path} must contain an object")
    return value


def task_manifest_paths() -> list[Path]:
    return sorted(TASKS_ROOT.glob("*.yaml"))


def status_porcelain(cwd: Path = REPO_ROOT) -> list[str]:
    output = git_output("status", "--porcelain", cwd=cwd)
    return output.splitlines() if output else []


def staged_status_lines(status_lines: Iterable[str]) -> list[str]:
    return [
        line for line in status_lines
        if len(line) >= 2 and line[0] not in {" ", "?"}
    ]


def is_protected_owner_path(path: str | Path, registry: dict[str, Any] | None = None) -> bool:
    if registry is None:
        registry = load_json_compatible_yaml(GOVERNANCE_ROOT / "WORKSTREAM_OWNERSHIP.yaml")
    candidate = normalize_path(Path(path).resolve())
    for protected in registry.get("policy", {}).get("protected_owner_paths", []):
        protected_path = normalize_path(Path(str(protected)).resolve())
        if candidate.casefold() == protected_path.casefold():
            return True
        if candidate.casefold().startswith((protected_path + "/").casefold()):
            return True
    return False


def emit_errors(errors: list[str], *, success_message: str) -> int:
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"PASS: {success_message}")
    return 0
