from pathlib import Path

from infra.scripts.phase1_bundle_report import build_report

from topicpilot_api.bundle import load_bundle

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def test_phase1_demo_bundle_report_is_complete_and_non_formal() -> None:
    bundle = load_bundle(REPOSITORY_ROOT / "fixtures" / "demo")
    report = build_report(bundle)

    assert report["source"]["classification"] == "PUBLIC_SYNTHETIC"
    assert report["source"]["formalDataImported"] is False
    assert report["counts"]["stocks"] == 4
    assert report["counts"]["topics"] == 4
    assert report["counts"]["stockTopicRelations"] == 5
    assert report["checks"]["allForeignKeysValid"] is True
    assert report["checks"]["formalDataImported"] is False
    assert report["checks"]["newsEntitiesInV1Contract"] is False
