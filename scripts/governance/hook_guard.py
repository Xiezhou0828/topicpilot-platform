from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

from _lib import is_protected_owner_path

MUTATION = re.compile(
    r"(?ix)"
    r"\bgit\s+(add|commit|stash|reset|restore|clean|checkout|switch|merge|rebase|cherry-pick|push|pull)\b"
    r"|\b(remove-item|move-item|set-content|add-content|out-file|clear-content|del|erase|rmdir|rm|mv|cp|new-item)\b"
    r"|\bnpm\s+(ci|install|run\s+(build|dev))\b"
    r"|\bpython\s+-m\s+pip\s+install\b"
)


def payload_value(payload: dict[str, Any], *names: str) -> Any:
    for name in names:
        if name in payload:
            return payload[name]
    return None


def is_mutating_tool(tool_name: str, tool_args: Any) -> bool:
    lowered = tool_name.lower()
    if lowered in {"edit", "write", "create", "str_replace_editor", "apply_patch"}:
        return True
    if lowered not in {"bash", "powershell", "shell", "execute"}:
        return False
    try:
        serialized = json.dumps(tool_args, ensure_ascii=False)
    except TypeError:
        serialized = str(tool_args)
    return bool(MUTATION.search(serialized))


def protected_path_hint(value: str) -> bool:
    normalized = value.replace("\\", "/").casefold()
    return normalized.startswith("c:/users/acer/desktop/") and normalized.endswith("/topicpilot-platform")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError) as exc:
        print(json.dumps({
            "permissionDecision": "deny",
            "permissionDecisionReason": f"invalid hook payload: {exc}",
        }))
        return 0

    cwd = payload_value(payload, "cwd")
    tool_name = str(payload_value(payload, "toolName", "tool_name") or "")
    tool_args = payload_value(payload, "toolArgs", "tool_input")
    args_text = json.dumps(tool_args, ensure_ascii=False) if tool_args is not None else ""
    protected_cwd = bool(cwd and (is_protected_owner_path(Path(str(cwd))) or protected_path_hint(str(cwd))))
    protected_argument = (
        "C:\\Users\\acer\\Desktop\\題材領航\\topicpilot-platform".casefold() in args_text.casefold()
        or protected_path_hint(args_text)
    )
    if (protected_cwd or protected_argument) and is_mutating_tool(tool_name, tool_args):
        print(json.dumps({
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "Mutation is blocked in the protected C: owner checkout. "
                "Use a named E: worktree and a governed task manifest."
            ),
        }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
