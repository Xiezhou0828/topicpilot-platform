from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.governance
ROOT = Path(__file__).resolve().parents[3]
CHECK_PATH = ROOT / "infra" / "scripts" / "check_system_of_record_boundaries.py"
SPEC = importlib.util.spec_from_file_location("system_of_record_check", CHECK_PATH)
assert SPEC is not None and SPEC.loader is not None
CHECK = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CHECK
SPEC.loader.exec_module(CHECK)


def _temporary_repository(tmp_path: Path, source: str) -> Path:
    package = tmp_path / "services" / "api" / "src" / "topicpilot_api"
    package.mkdir(parents=True)
    (package / "consumer.py").write_text(source, encoding="utf-8")
    resolver = package / "topic_engine" / "structural_role_authority.py"
    resolver.parent.mkdir()
    resolver.write_text("# canonical resolver\n", encoding="utf-8")
    orm = package / "orm" / "models.py"
    orm.parent.mkdir()
    orm.write_text("class InstrumentTopicRelation: ...\n", encoding="utf-8")
    return tmp_path


def test_repository_has_no_formal_system_of_record_boundary_violations() -> None:
    assert CHECK.inspect(ROOT) == ()


@pytest.mark.parametrize(
    ("source", "metric"),
    [
        ('SOURCE = "reports/old/current.json"\n', "FORMAL_RUNTIME_DEPENDS_ON_REPORTS"),
        ("from topicpilot_api.research.model import value\n", "FORMAL_RUNTIME_DEPENDS_ON_RESEARCH"),
        (
            "from topicpilot_api.opportunity_shadow import Evidence\n",
            "FORMAL_RUNTIME_DEPENDS_ON_SHADOW",
        ),
        (
            "from topicpilot_api.orm.models import InstrumentTopicRelation\n"
            "FIELD = InstrumentTopicRelation.structural_role\n",
            "FORMAL_AUTHORITY_BYPASS_PATHS",
        ),
        ("CURRENT_TOPIC_COUNT = 460\n", "HARDCODED_CURRENT_TOPIC_COUNT"),
    ],
)
def test_check_fails_closed_for_each_governed_boundary(
    tmp_path: Path, source: str, metric: str
) -> None:
    violations = CHECK.inspect(_temporary_repository(tmp_path, source))
    assert metric in {item.metric for item in violations}
