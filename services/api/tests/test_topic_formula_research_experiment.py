import copy
import json
import shutil
from dataclasses import replace
from pathlib import Path

import pytest

from topicpilot_api.research_cli import main as research_cli_main
from topicpilot_api.topic_engine import (
    FormulaResearchValidationError,
    export_formula_research_experiment_manifest,
    export_formula_research_experiment_report,
    load_formula_research_experiment,
    run_formula_research_experiment,
)

pytestmark = pytest.mark.research

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "fixtures" / "research"
MANIFEST = FIXTURE_DIR / "topic_formula_experiment.v1.json"
CORPUS = FIXTURE_DIR / "topic_formula_candidate_evidence.v1.json"


def _document():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def _write_bundle(tmp_path, document):
    tmp_path.mkdir(parents=True, exist_ok=True)
    manifest = tmp_path / MANIFEST.name
    manifest.write_text(json.dumps(document, indent=2), encoding="utf-8")
    shutil.copyfile(CORPUS, tmp_path / CORPUS.name)
    return manifest


def test_manifest_loads_canonically_and_candidate_order_is_irrelevant(tmp_path):
    original = load_formula_research_experiment(MANIFEST)
    reordered = _document()
    reordered["candidates"].reverse()
    for candidate in reordered["candidates"]:
        candidate["sourceReferences"].reverse()
    repeated = load_formula_research_experiment(_write_bundle(tmp_path, reordered))

    assert original == repeated
    assert len(original.manifest_digest) == 64
    assert [spec.candidate_id for spec in original.candidate_specs] == [
        "diffusion-participation-baseline",
        "strict-participation-baseline",
    ]
    assert json.loads(export_formula_research_experiment_manifest(original)) == _document()


def test_manifest_tampering_corpus_mismatch_and_unsafe_paths_fail_closed(tmp_path):
    tampered = _document()
    tampered["candidates"][0]["breadth"]["weight"] = 0.4
    with pytest.raises(FormulaResearchValidationError):
        load_formula_research_experiment(_write_bundle(tmp_path / "tampered", tampered))

    mismatch = _document()
    mismatch["corpus"]["contentDigest"] = "0" * 64
    with pytest.raises(FormulaResearchValidationError):
        load_formula_research_experiment(_write_bundle(tmp_path / "mismatch", mismatch))

    for index, unsafe in enumerate(("../outside.json", "C:/outside.json", "folder\\file.json")):
        document = _document()
        document["corpus"]["file"] = unsafe
        with pytest.raises(FormulaResearchValidationError, match="corpus file"):
            load_formula_research_experiment(_write_bundle(tmp_path / f"unsafe-{index}", document))


def test_experiment_report_is_deterministic_complete_and_unranked():
    experiment = load_formula_research_experiment(MANIFEST)
    first = run_formula_research_experiment(experiment)
    repeated = run_formula_research_experiment(experiment)
    first_report = export_formula_research_experiment_report(first)

    assert first == repeated
    assert first_report == export_formula_research_experiment_report(repeated)
    assert len(first.experiment_digest) == 64
    document = json.loads(first_report)
    assert document["mode"] == "RESEARCH_ONLY"
    assert document["manifestDigest"] == experiment.manifest_digest
    assert len(document["caseAnalyses"]) == len(experiment.corpus.cases) == 4
    replay_by_case = {
        item["caseId"]: item["replayDigest"] for item in document["corpusRun"]["cases"]
    }
    for item in document["caseAnalyses"]:
        assert item["analysis"]["source"]["replayDigest"] == replay_by_case[item["caseId"]]
    lowered = first_report.lower()
    for forbidden in (
        "callable",
        "credential",
        "futurereturn",
        "productiondefault",
        "ranking",
        "winner",
    ):
        assert forbidden not in lowered


def test_report_rejects_digest_or_analysis_lineage_tampering():
    experiment = load_formula_research_experiment(MANIFEST)
    result = run_formula_research_experiment(experiment)

    with pytest.raises(FormulaResearchValidationError, match="report digest"):
        export_formula_research_experiment_report(replace(result, experiment_digest="0" * 64))

    first_analysis = result.case_analyses[0]
    bad_analysis = replace(first_analysis.analysis, source_replay_digest="0" * 64)
    bad_result = replace(
        result,
        case_analyses=(replace(first_analysis, analysis=bad_analysis), *result.case_analyses[1:]),
    )
    with pytest.raises(FormulaResearchValidationError):
        export_formula_research_experiment_report(bad_result)


def test_cli_replay_is_byte_identical(tmp_path, capsys):
    first = tmp_path / "first" / "report.json"
    second = tmp_path / "second" / "report.json"

    assert research_cli_main(["--manifest", str(MANIFEST), "--output", str(first)]) == 0
    assert research_cli_main(["--manifest", str(MANIFEST), "--output", str(second)]) == 0
    assert first.read_bytes() == second.read_bytes()
    assert json.loads(first.read_text(encoding="utf-8"))["mode"] == "RESEARCH_ONLY"
    assert "research-only report" in capsys.readouterr().out


def test_unknown_manifest_fields_and_duplicate_candidates_fail_closed(tmp_path):
    unknown = _document()
    unknown["unexpected"] = True
    with pytest.raises(FormulaResearchValidationError, match="fields"):
        load_formula_research_experiment(_write_bundle(tmp_path / "unknown", unknown))

    duplicate = _document()
    duplicate["candidates"].append(copy.deepcopy(duplicate["candidates"][0]))
    with pytest.raises(FormulaResearchValidationError, match="unique"):
        load_formula_research_experiment(_write_bundle(tmp_path / "duplicate", duplicate))
