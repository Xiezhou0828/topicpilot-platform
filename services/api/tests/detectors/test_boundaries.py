"""Architecture boundary tests for the detector framework.

These tests inspect imports statically so they do not need to import the API,
ORM, repository, or persistence layers while checking the detector boundary.
"""

from __future__ import annotations

import ast
from pathlib import Path


DETECTOR_PACKAGE = "topicpilot_api.detectors"
DETECTOR_SOURCE = (
    Path(__file__).resolve().parents[2] / "src" / "topicpilot_api" / "detectors"
)

FORBIDDEN_PREFIXES = (
    "topicpilot_api.orm",
    "topicpilot_api.models",
    "sqlalchemy",
    "topicpilot_api.repository",
    "topicpilot_api.repositories",
    "topicpilot_api.persistence",
    "topicpilot_api.main",
    "topicpilot_api.api",
    "topicpilot_api.schemas",
    "topicpilot_api.problems",
)


def _imported_modules(source: Path) -> set[str]:
    """Return absolute module names imported by a Python source file."""
    tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                modules.add(node.module)
            elif node.level:
                # Resolve only imports that stay within the detector package.
                parts = source.relative_to(DETECTOR_SOURCE).with_suffix("").parts
                package_parts = tuple(DETECTOR_PACKAGE.split(".")) + parts[:-1]
                anchor = max(0, len(package_parts) - node.level + 1)
                module = ".".join(package_parts[:anchor])
                if node.module:
                    module = f"{module}.{node.module}"
                modules.add(module)
    return modules


def _all_detector_imports() -> set[str]:
    imports: set[str] = set()
    for source in DETECTOR_SOURCE.glob("*.py"):
        imports.update(_imported_modules(source))
    return imports


def test_detector_package_does_not_import_forbidden_layers():
    imported = _all_detector_imports()
    violations = sorted(
        module
        for module in imported
        if any(module == prefix or module.startswith(prefix + ".") for prefix in FORBIDDEN_PREFIXES)
    )
    assert not violations, f"detector package imports forbidden layers: {violations}"


def test_detector_package_local_dependencies_stay_inside_detector_package():
    imported = _all_detector_imports()
    local_imports = sorted(
        module
        for module in imported
        if module.startswith("topicpilot_api.")
        and not module.startswith(DETECTOR_PACKAGE)
    )
    assert not local_imports, (
        "detector package local dependencies must point only to "
        f"{DETECTOR_PACKAGE}: {local_imports}"
    )


def test_detector_package_source_is_present_for_boundary_scan():
    assert DETECTOR_SOURCE.is_dir()
    assert any(DETECTOR_SOURCE.glob("*.py"))
