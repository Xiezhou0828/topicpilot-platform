"""Offline generation and validation command for canonical reference bundles."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from topicpilot_api.reference_data import (
    BUNDLE_FILE_NAMES,
    BundleValidationError,
    build_bundle_from_sources,
    load_bundle,
    write_bundle,
)


def _append_semantic_differences(
    expected: object,
    actual: object,
    path: str,
    differences: list[dict[str, object]],
    *,
    limit: int = 20,
) -> None:
    if len(differences) >= limit:
        return
    if type(expected) is not type(actual):
        differences.append({"semanticPath": path, "expected": expected, "actual": actual})
        return
    if isinstance(expected, dict) and isinstance(actual, dict):
        for key in sorted(set(expected) | set(actual)):
            if key not in expected or key not in actual:
                differences.append(
                    {
                        "semanticPath": f'{path}[{json.dumps(key, ensure_ascii=False)}]',
                        "expected": expected.get(key),
                        "actual": actual.get(key),
                    }
                )
            else:
                _append_semantic_differences(
                    expected[key],
                    actual[key],
                    f'{path}[{json.dumps(key, ensure_ascii=False)}]',
                    differences,
                    limit=limit,
                )
            if len(differences) >= limit:
                return
        return
    if isinstance(expected, list) and isinstance(actual, list):
        for index in range(max(len(expected), len(actual))):
            if index >= len(expected) or index >= len(actual):
                differences.append(
                    {
                        "semanticPath": f"{path}[{index}]",
                        "expected": expected[index] if index < len(expected) else None,
                        "actual": actual[index] if index < len(actual) else None,
                    }
                )
            else:
                _append_semantic_differences(
                    expected[index], actual[index], f"{path}[{index}]", differences, limit=limit
                )
            if len(differences) >= limit:
                return
        return
    if expected != actual:
        differences.append({"semanticPath": path, "expected": expected, "actual": actual})


def _compare_bundle_bytes(
    expected_dir: Path, generated_dir: Path
) -> tuple[list[str], list[dict[str, object]]]:
    changed_artifacts: list[str] = []
    differences: list[dict[str, object]] = []
    for filename in ("manifest.json", *BUNDLE_FILE_NAMES):
        expected_path = expected_dir / filename
        generated_path = generated_dir / filename
        if expected_path.read_bytes() == generated_path.read_bytes():
            continue
        changed_artifacts.append(filename)
        try:
            expected = json.loads(expected_path.read_text(encoding="utf-8"))
            actual = json.loads(generated_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            differences.append(
                {
                    "artifactPath": filename,
                    "semanticPath": "$",
                    "expected": "byte content",
                    "actual": "different byte content",
                }
            )
        else:
            before = len(differences)
            _append_semantic_differences(expected, actual, "$", differences)
            for item in differences[before:]:
                item["artifactPath"] = filename
    return changed_artifacts, differences


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    generate = commands.add_parser(
        "generate", help="generate a canonical bundle from approved inputs"
    )
    generate.add_argument("--stock-source", type=Path, required=True)
    generate.add_argument("--calendar-source", type=Path, required=True)
    generate.add_argument("--evidence-source", type=Path, required=True)
    generate.add_argument(
        "--adjustment-source",
        type=Path,
        default=Path(__file__).with_name("reference_data")
        / "governance"
        / "adjustment_catalogue.json",
    )
    generate.add_argument("--reference-version", default="tw-reference-v1")
    generate.add_argument("--output-dir", type=Path, required=True)
    validate = commands.add_parser("validate", help="validate an existing canonical bundle")
    validate.add_argument("--bundle-dir", type=Path, required=True)
    check = commands.add_parser(
        "check",
        help="prove an existing bundle matches canonical generation or serialization",
    )
    check.add_argument("--bundle-dir", type=Path, required=True)
    check.add_argument("--stock-source", type=Path)
    check.add_argument("--calendar-source", type=Path)
    check.add_argument("--evidence-source", type=Path)
    check.add_argument("--adjustment-source", type=Path)
    check.add_argument("--reference-version")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "generate":
            bundle = build_bundle_from_sources(
                stock_source=args.stock_source,
                calendar_source=args.calendar_source,
                evidence_source=args.evidence_source,
                adjustment_source=args.adjustment_source,
                version=args.reference_version,
            )
            output_dir = write_bundle(bundle, args.output_dir)
            output = {"operation": "GENERATED", "bundleDir": str(output_dir), **bundle.summary()}
        elif args.command == "validate":
            bundle = load_bundle(args.bundle_dir)
            output = {
                "operation": "VALIDATED",
                "bundleDir": str(args.bundle_dir),
                **bundle.summary(),
            }
        else:
            bundle = load_bundle(args.bundle_dir)
            with tempfile.TemporaryDirectory(prefix="topicpilot-reference-check-") as temp_dir:
                generated_dir = write_bundle(bundle, Path(temp_dir))
                source_args = (
                    args.stock_source,
                    args.calendar_source,
                    args.evidence_source,
                )
                if any(source_args) and not all(source_args):
                    raise BundleValidationError(
                        "check source inputs must include stock, calendar, and evidence"
                    )
                if all(source_args):
                    generated = build_bundle_from_sources(
                        stock_source=args.stock_source,
                        calendar_source=args.calendar_source,
                        evidence_source=args.evidence_source,
                        adjustment_source=(
                            args.adjustment_source
                            or Path(__file__).with_name("reference_data")
                            / "governance"
                            / "adjustment_catalogue.json"
                        ),
                        version=(
                            args.reference_version
                            or bundle.manifest["referenceDataVersion"]
                        ),
                    )
                    generated_dir = write_bundle(generated, Path(temp_dir) / "generated")
                changed_artifacts, differences = _compare_bundle_bytes(
                    args.bundle_dir, generated_dir
                )
            matches = not changed_artifacts
            output = {
                "operation": "CHECKED",
                "bundleDir": str(args.bundle_dir),
                "CURRENT_BUNDLE_MATCHES_CANONICAL_GENERATOR": "YES" if matches else "NO",
                "changedArtifacts": changed_artifacts,
                "differences": differences,
                **bundle.summary(),
            }
            if not matches:
                print(json.dumps(output, ensure_ascii=False, sort_keys=True))
                return 2
    except BundleValidationError as exc:
        print(json.dumps({"status": "BLOCKED", "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(output, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
