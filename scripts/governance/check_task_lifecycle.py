from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from _lib import GOVERNANCE_ROOT, emit_errors, load_json_compatible_yaml, load_manifest
from check_task_manifest import validate_manifest


def validate_transition(from_state: str, to_state: str, contract: dict[str, Any] | None = None) -> list[str]:
    contract = contract or load_json_compatible_yaml(GOVERNANCE_ROOT / "task_lifecycle.json")
    if from_state not in contract.get("statuses", []):
        return [f"invalid source status {from_state}"]
    if to_state not in contract.get("statuses", []):
        return [f"invalid target status {to_state}"]
    if to_state not in contract.get("transitions", {}).get(from_state, []):
        return [f"illegal transition {from_state} -> {to_state}"]
    return []


def validate_manifest_lifecycle(manifest: dict[str, Any], source: str = "<manifest>") -> list[str]:
    errors = validate_manifest(manifest, source=source)
    status = manifest.get("status")
    if status == "READY_FOR_INTEGRATION" and not manifest.get("implementation_commits"):
        errors.append(f"{source}: READY_FOR_INTEGRATION without implementation evidence")
    if status == "ABANDONED" and not (
        manifest.get("disposition_evidence") or manifest.get("supersedes")
    ):
        errors.append(f"{source}: ABANDONED without decision or supersession evidence")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate task lifecycle states and transitions.")
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--from-state")
    parser.add_argument("--to-state")
    args = parser.parse_args()
    errors: list[str] = []
    if args.from_state or args.to_state:
        if not (args.from_state and args.to_state):
            errors.append("--from-state and --to-state must be supplied together")
        else:
            errors.extend(validate_transition(args.from_state, args.to_state))
    if args.manifest:
        try:
            manifest = load_manifest(args.manifest)
            errors.extend(validate_manifest_lifecycle(manifest, str(args.manifest)))
        except (OSError, ValueError) as exc:
            errors.append(str(exc))
    if not args.manifest and not args.from_state:
        errors.append("provide --manifest or a state transition")
    return emit_errors(errors, success_message="lifecycle contract is valid")


if __name__ == "__main__":
    raise SystemExit(main())
