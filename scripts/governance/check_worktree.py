from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from typing import Any

from _lib import (
    emit_errors,
    git_output,
    is_protected_owner_path,
    load_manifest,
    status_porcelain,
)


def validate_worktree(
    manifest: dict[str, Any],
    *,
    cwd: Path,
    branch: str | None = None,
    require_clean: bool = False,
) -> list[str]:
    errors: list[str] = []
    cwd = cwd.resolve()
    if is_protected_owner_path(cwd):
        errors.append("mutation task is running inside the protected C: owner checkout")

    expected_worktree = manifest.get("worktree")
    if expected_worktree:
        if cwd != Path(str(expected_worktree)).resolve():
            errors.append(
                f"worktree mismatch: expected {expected_worktree}, actual {cwd}"
            )
    elif manifest.get("status") in {"IN_PROGRESS", "READY_FOR_INTEGRATION", "INTEGRATED"}:
        errors.append("active mutation task has no worktree")

    expected_branch = manifest.get("branch")
    if branch is None:
        try:
            branch = git_output("branch", "--show-current", cwd=cwd)
        except (OSError, subprocess.CalledProcessError):
            branch = None
    if expected_branch and branch != expected_branch:
        errors.append(f"branch mismatch: expected {expected_branch}, actual {branch!r}")

    base_sha = manifest.get("base_sha")
    if base_sha:
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", base_sha, "HEAD"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            errors.append(f"base SHA is not an ancestor of HEAD: {base_sha}")

    status = status_porcelain(cwd)
    if require_clean and status:
        errors.append(f"worktree is not clean: {len(status)} status entries")
    if require_clean and any(line[:1] != " " and line[:1] != "?" for line in status):
        errors.append("staged changes are not allowed at clean-check phase")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Check task branch and worktree boundaries.")
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--require-clean", action="store_true")
    args = parser.parse_args()
    manifest = load_manifest(args.manifest)
    errors = validate_worktree(
        manifest,
        cwd=Path.cwd(),
        require_clean=args.require_clean,
    )
    return emit_errors(errors, success_message="branch, worktree, ancestry, and state are valid")


if __name__ == "__main__":
    raise SystemExit(main())
