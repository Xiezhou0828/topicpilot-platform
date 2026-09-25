"""Fail CI closed for malformed or multi-head Alembic migration history."""

from __future__ import annotations

import sys
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_CONFIG = ROOT / "services" / "api" / "alembic.ini"


def _references(
    value: str | list[str] | tuple[str, ...] | None,
) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    return tuple(value)


def inspect_graph(
    config_path: Path = ALEMBIC_CONFIG,
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    """Return revision IDs, heads, and graph-integrity violations."""
    script = ScriptDirectory.from_config(Config(str(config_path)))
    revisions = tuple(script.walk_revisions(base="base", head="heads"))
    revision_ids = tuple(revision.revision for revision in revisions)
    known_ids = set(revision_ids)
    violations: list[str] = []

    if len(revision_ids) != len(known_ids):
        duplicates = sorted(
            revision_id
            for revision_id in known_ids
            if revision_ids.count(revision_id) > 1
        )
        violations.append(
            f"duplicate revision identifiers: {', '.join(duplicates)}"
        )

    for revision in revisions:
        for field in ("down_revision", "dependencies"):
            for reference in _references(getattr(revision, field)):
                if reference not in known_ids:
                    violations.append(
                        f"{revision.revision} has unresolved/non-full "
                        f"{field} reference {reference!r}"
                    )

    heads = tuple(script.get_heads())
    if len(heads) != 1:
        head_list = ", ".join(heads) or "(none)"
        violations.append(
            "expected exactly one Alembic head, "
            f"found {len(heads)}: {head_list}"
        )

    return revision_ids, heads, tuple(violations)


def main() -> int:
    revision_ids, heads, violations = inspect_graph()

    print(f"ALEMBIC_REVISION_COUNT={len(revision_ids)}")
    print(f"ALEMBIC_HEAD_COUNT={len(heads)}")
    if violations:
        print("ALEMBIC_GRAPH_STATUS=FAIL", file=sys.stderr)
        for violation in violations:
            print(f"ALEMBIC_GRAPH_VIOLATION={violation}", file=sys.stderr)
        return 1

    print(f"ALEMBIC_HEAD={heads[0]}")
    print("ALEMBIC_GRAPH_STATUS=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
