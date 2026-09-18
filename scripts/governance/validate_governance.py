from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path

from _lib import (
    GOVERNANCE_ROOT,
    REPO_ROOT,
    emit_errors,
    load_json_compatible_yaml,
    load_manifest,
)
from check_task_manifest import validate_manifests
from check_task_ownership import ownership_errors
from check_worktree import validate_worktree


def validate_baseline_registry() -> list[str]:
    errors: list[str] = []
    path = GOVERNANCE_ROOT / "BASELINE_FAILURE_REGISTRY.yaml"
    try:
        registry = load_json_compatible_yaml(path)
    except (OSError, ValueError) as exc:
        return [str(exc)]
    required = {
        "test_id",
        "first_observed",
        "owner_workstream",
        "classification",
        "evidence",
        "blocks_workstreams",
        "expires_or_recheck",
        "resolved_by",
    }
    for index, entry in enumerate(registry.get("failures", []), start=1):
        missing = sorted(required - set(entry))
        errors.extend(f"{path}: failure {index} missing {field}" for field in missing)
        expiry = entry.get("expires_or_recheck")
        if expiry:
            try:
                expiry_date = dt.date.fromisoformat(str(expiry))
            except ValueError:
                errors.append(f"{path}: invalid expires_or_recheck {expiry!r}")
            else:
                if expiry_date < dt.datetime.now(dt.timezone.utc).date() and not entry.get("resolved_by"):
                    errors.append(f"STALE_BASELINE_FAILURE: {entry.get('test_id')}")
    return errors


def validate_registry_shapes() -> list[str]:
    errors: list[str] = []
    ownership_path = GOVERNANCE_ROOT / "WORKSTREAM_OWNERSHIP.yaml"
    try:
        registry = load_json_compatible_yaml(ownership_path)
    except (OSError, ValueError) as exc:
        return [str(exc)]
    required_workstreams = {"GOVERNANCE", "TODAY", "A10_A9", "TOPIC_B2", "OPPORTUNITY", "RELEASE", "INTEGRATION"}
    actual = set(registry.get("workstreams", {}))
    errors.extend(
        f"{ownership_path}: missing workstream {name}"
        for name in sorted(required_workstreams - actual)
    )
    return errors


def validate_customization_surfaces() -> list[str]:
    errors: list[str] = []
    skills_root = REPO_ROOT / ".github" / "skills"
    for skill_dir in sorted(skills_root.iterdir()) if skills_root.exists() else []:
        if not skill_dir.is_dir():
            continue
        path = skill_dir / "SKILL.md"
        if not path.exists():
            errors.append(f"missing SKILL.md: {path}")
            continue
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---\n") or "\n---\n" not in text[4:]:
            errors.append(f"skill frontmatter missing: {path}")
            continue
        frontmatter = text[4:].split("\n---\n", 1)[0]
        if "name:" not in frontmatter or "description:" not in frontmatter:
            errors.append(f"skill frontmatter requires name and description: {path}")
        if "<TODO>" in text or "<PLACEHOLDER>" in text:
            errors.append(f"unfinished skill scaffold: {path}")

    agents_root = REPO_ROOT / ".github" / "agents"
    for path in sorted(agents_root.glob("*.agent.md")) if agents_root.exists() else []:
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---\n") or "\n---\n" not in text[4:]:
            errors.append(f"agent frontmatter missing: {path}")
            continue
        frontmatter = text[4:].split("\n---\n", 1)[0]
        if "description:" not in frontmatter:
            errors.append(f"agent description missing: {path}")

    hooks_root = REPO_ROOT / ".github" / "hooks"
    for path in sorted(hooks_root.glob("*.json")) if hooks_root.exists() else []:
        try:
            hook = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"invalid hook file {path}: {exc}")
            continue
        if hook.get("version") != 1 or not isinstance(hook.get("hooks"), dict):
            errors.append(f"hook file requires version 1 and hooks object: {path}")
        for event, entries in hook.get("hooks", {}).items():
            if not isinstance(entries, list):
                errors.append(f"hook event must be a list: {path}:{event}")
                continue
            for entry in entries:
                if entry.get("type", "command") == "command" and not any(
                    key in entry for key in ("bash", "powershell", "command", "exec")
                ):
                    errors.append(f"command hook has no executable command: {path}:{event}")

    governance_workflow = REPO_ROOT / ".github" / "workflows" / "governance.yml"
    if governance_workflow.exists() and "merge_group:" not in governance_workflow.read_text(encoding="utf-8"):
        errors.append("governance workflow must include merge_group for integration candidates")
    return errors


def self_test() -> list[str]:
    from check_release_gate import evaluate_migration_lineage
    from check_task_lifecycle import validate_transition

    errors: list[str] = []
    if not validate_transition("PLANNED", "IN_PROGRESS"):
        pass
    else:
        errors.append("self-test: legal PLANNED -> IN_PROGRESS transition failed")
    if not validate_transition("DEPLOYED", "IMPLEMENTED"):
        errors.append("self-test: illegal transition was accepted")
    migration = evaluate_migration_lineage(
        "0039_task_a9_b2_formal_correction_supersession",
        "0040_task_a10_recovery_checkpoint_observability",
    )
    if migration["status"] != "BLOCKED_MIGRATION":
        errors.append("self-test: newer Production migration was not blocked")
    return errors


def session_start_errors() -> list[str]:
    task_id = os.environ.get("TOPICPILOT_TASK_ID")
    if not task_id:
        return []
    path = GOVERNANCE_ROOT / "tasks" / f"{task_id}.yaml"
    if not path.exists():
        return [f"session task manifest not found: {task_id}"]
    manifest = load_manifest(path)
    return validate_worktree(manifest, cwd=Path.cwd(), require_clean=False)


def main() -> int:
    parser = argparse.ArgumentParser(description="Aggregate TopicPilot governance validation.")
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--paths", action="append", default=[])
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--session-start", action="store_true")
    args = parser.parse_args()

    errors: list[str] = []
    _, manifest_errors = validate_manifests()
    errors.extend(manifest_errors)
    errors.extend(validate_baseline_registry())
    errors.extend(validate_registry_shapes())
    errors.extend(validate_customization_surfaces())

    if args.manifest:
        manifest = load_manifest(args.manifest)
        errors.extend(ownership_errors(manifest, args.paths))
        if args.session_start:
            errors.extend(validate_worktree(manifest, cwd=Path.cwd(), require_clean=False))
    elif args.paths:
        errors.append("--paths requires --manifest")

    if args.session_start:
        errors.extend(session_start_errors())

    if args.self_test:
        errors.extend(self_test())

    return emit_errors(
        errors,
        success_message="governance manifests, registries, lifecycle, and baseline registry are valid",
    )


if __name__ == "__main__":
    raise SystemExit(main())
