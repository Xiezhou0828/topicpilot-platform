"""Enforce formal runtime system-of-record boundaries.

This check deliberately inspects code, not historical documents.  Reports,
research fixtures, and shadow implementations may exist, but formal runtime
consumers must not import or read them as authority.
"""

from __future__ import annotations

import ast
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
API_PACKAGE = ROOT / "services" / "api" / "src" / "topicpilot_api"

# These are intentionally non-formal surfaces.  They may consume evidence-only
# inputs, but formal runtime files may not depend on them.
FORMAL_EXCLUSIONS = {
    API_PACKAGE / "research_cli.py",
    API_PACKAGE / "opportunity_shadow_api.py",
    API_PACKAGE / "opportunity_shadow_read.py",
    API_PACKAGE / "topic_engine" / "opportunity_contract.py",
    API_PACKAGE / "topic_engine" / "opportunity_evidence.py",
    API_PACKAGE / "topic_engine" / "opportunity_qualification.py",
    API_PACKAGE / "topic_engine" / "opportunity_strategies.py",
}
CANONICAL_AUTHORITY_RESOLVER = (
    API_PACKAGE / "topic_engine" / "structural_role_authority.py"
)
ALLOWED_DIRECT_RELATION_READERS = {
    CANONICAL_AUTHORITY_RESOLVER,
    API_PACKAGE / "orm" / "models.py",
}

CURRENT_TOPIC_COUNT = re.compile(
    r"(?:CURRENT|EXPECTED|FORMAL|PRODUCTION)_TOPIC_COUNT\s*=\s*\d+",
    re.IGNORECASE,
)
FORBIDDEN_PATH = re.compile(
    r"(?:^|[/'\"])(?:reports|fixtures/research|docs/research)(?:[/'\"]|$)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Violation:
    metric: str
    path: Path
    line: int
    detail: str

    def render(self) -> str:
        relative = self.path.relative_to(ROOT).as_posix()
        return f"{self.metric}: {relative}:{self.line}: {self.detail}"


def _is_formal_runtime(path: Path) -> bool:
    if (
        path in FORMAL_EXCLUSIONS
        or "research" in path.parts
        or path.name.startswith("research_")
        or path.name in {"research.py", "historical_validation.py"}
        or path.name == "__init__.py"
    ):
        return False
    return path.suffix == ".py" and API_PACKAGE in path.parents


def _import_names(tree: ast.AST) -> tuple[tuple[int, str], ...]:
    names: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend((node.lineno, alias.name) for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append((node.lineno, node.module))
    return tuple(names)


def inspect(root: Path = ROOT) -> tuple[Violation, ...]:
    api_package = root / "services" / "api" / "src" / "topicpilot_api"
    resolver = api_package / "topic_engine" / "structural_role_authority.py"
    allowed_relation_readers = {resolver, api_package / "orm" / "models.py"}
    exclusions = {
        api_package / "research_cli.py",
        api_package / "opportunity_shadow_api.py",
        api_package / "opportunity_shadow_read.py",
        api_package / "topic_engine" / "opportunity_contract.py",
        api_package / "topic_engine" / "opportunity_evidence.py",
        api_package / "topic_engine" / "opportunity_qualification.py",
        api_package / "topic_engine" / "opportunity_strategies.py",
    }
    violations: list[Violation] = []

    for path in sorted(api_package.rglob("*.py")):
        if (
            path in exclusions
            or "research" in path.parts
            or path.name.startswith("research_")
            or path.name in {"research.py", "historical_validation.py"}
            or path.name == "__init__.py"
        ):
            continue
        text = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(text, filename=str(path))
        except SyntaxError as exc:
            violations.append(Violation("FORMAL_RUNTIME_PARSE_ERROR", path, exc.lineno or 1, str(exc)))
            continue

        for line, module in _import_names(tree):
            parts = set(re.split(r"[._]", module))
            if "research" in parts:
                violations.append(Violation("FORMAL_RUNTIME_DEPENDS_ON_RESEARCH", path, line, module))
            if "shadow" in parts and not (
                path == api_package / "main.py"
                and module == "topicpilot_api.opportunity_shadow_api"
            ):
                violations.append(Violation("FORMAL_RUNTIME_DEPENDS_ON_SHADOW", path, line, module))

        for node in ast.walk(tree):
            if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
                continue
            value = node.value.replace("\\", "/")
            if FORBIDDEN_PATH.search(value):
                metric = (
                    "FORMAL_RUNTIME_DEPENDS_ON_REPORTS"
                    if "reports" in value.lower()
                    else "FORMAL_RUNTIME_DEPENDS_ON_RESEARCH"
                )
                violations.append(Violation(metric, path, node.lineno, value))

        if (
            path not in allowed_relation_readers
            and re.search(r"\bInstrumentTopicRelation\b", text)
            and re.search(r"InstrumentTopicRelation\.structural_role\b", text)
        ):
            violations.append(
                Violation(
                    "FORMAL_AUTHORITY_BYPASS_PATHS",
                    path,
                    1,
                    "direct relation access must use resolve_structural_role",
                )
            )
        match = CURRENT_TOPIC_COUNT.search(text)
        if match:
            violations.append(
                Violation("HARDCODED_CURRENT_TOPIC_COUNT", path, text[: match.start()].count("\n") + 1, match.group())
            )

    return tuple(violations)


def main() -> int:
    violations = inspect()
    metrics = (
        "FORMAL_RUNTIME_DEPENDS_ON_REPORTS",
        "FORMAL_RUNTIME_DEPENDS_ON_RESEARCH",
        "FORMAL_RUNTIME_DEPENDS_ON_SHADOW",
        "FORMAL_AUTHORITY_BYPASS_PATHS",
        "HARDCODED_CURRENT_TOPIC_COUNT",
    )
    for metric in metrics:
        print(f"{metric}={sum(item.metric == metric for item in violations)}")
    for violation in violations:
        print(violation.render(), file=sys.stderr)
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
