"""Local command for deterministic, research-only Topic Formula experiments."""

from __future__ import annotations

import argparse
from pathlib import Path

from .topic_engine import (
    export_formula_research_experiment_report,
    load_formula_research_experiment,
    run_formula_research_experiment,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    experiment = load_formula_research_experiment(args.manifest)
    result = run_formula_research_experiment(experiment)
    report = export_formula_research_experiment_report(result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report + "\n", encoding="utf-8", newline="\n")
    print(f"research-only report: {args.output} ({result.experiment_digest})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
