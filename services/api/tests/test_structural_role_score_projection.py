from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import inspect

from topicpilot_api.orm import (
    InstrumentTopicRelation,
    TopicScoreProjection,
    TopicScoreProjectionMember,
)
from topicpilot_api.topic_engine import (
    AUTHORITY_READ_CURRENT,
    AUTHORITY_READ_HISTORICAL,
    SCORE_PROJECTION_READ_CURRENT,
    SCORE_PROJECTION_READ_HISTORICAL,
    STRUCTURAL_ROLE_CORE,
    STRUCTURAL_ROLE_RELATED,
    ScoreProjectionError,
    ScoreProjectionMemberRecord,
    ScoreProjectionRecord,
    StructuralRoleAuthorityError,
    StructuralRoleAuthorityRecord,
    build_governed_leader_set,
    resolve_score_projection_records,
    resolve_structural_role_records,
)

AS_OF = date(2026, 8, 7)


def _authority(
    instrument_id: str = "instrument-1",
    *,
    role: str = STRUCTURAL_ROLE_CORE,
    approval_state: str = "APPROVED",
    authority_id: str = "authority-1",
    authority_version: str = "roles.v1",
    effective_from: date = date(2026, 8, 1),
    effective_to: date | None = None,
    superseded_by: str | None = None,
) -> StructuralRoleAuthorityRecord:
    return StructuralRoleAuthorityRecord(
        authority_id=authority_id,
        topic_id="topic-1",
        instrument_id=instrument_id,
        structural_role=role,
        approval_state=approval_state,
        effective_from=effective_from,
        effective_to=effective_to,
        authority_version=authority_version,
        source_artifact_id="roles-artifact-v1",
        source_artifact_hash="a" * 64,
        approval_reference="owner-approval-1",
        correction_sequence=0,
        supersedes_authority_id=None,
        superseded_by_authority_id=superseded_by,
        lineage_hash="l" * 64,
    )


def _projection(
    *,
    instrument_id: str = "instrument-1",
    importance: Decimal = Decimal("1.00"),
    projection_id: str = "projection-1",
    projection_version: str = "projection.v1",
    approval_state: str = "APPROVED",
    source_version: str = "roles.v1",
    superseded_by: str | None = None,
) -> ScoreProjectionRecord:
    return ScoreProjectionRecord(
        projection_row_id="projection-row-1",
        topic_id="topic-1",
        projection_id=projection_id,
        projection_version=projection_version,
        effective_from=date(2026, 8, 1),
        effective_to=None,
        approval_state=approval_state,
        approval_reference="owner-projection-approval-1",
        source_structural_role_authority_id="roles-artifact-v1",
        source_structural_role_authority_version=source_version,
        selected_core_members=(
            ScoreProjectionMemberRecord(
                instrument_id=instrument_id,
                score_importance=importance,
                structural_role_authority_id="authority-1",
                structural_role_authority_version="roles.v1",
                member_lineage={"authorityId": "authority-1"},
            ),
        ),
        projection_lineage={"source": "roles-artifact-v1"},
        lineage_hash="p" * 64,
        correction_sequence=0,
        supersedes_projection_id=None,
        superseded_by_projection_id=superseded_by,
    )


def _resolve_authority(
    records: tuple[StructuralRoleAuthorityRecord, ...],
):
    def resolver(topic_id: str, instrument_id: str, as_of: date, *, read_mode: str):
        return resolve_structural_role_records(
            records,
            topic_id,
            instrument_id,
            as_of,
            read_mode=read_mode,
        )

    return resolver


def test_relation_and_projection_models_expose_formal_read_model_fields():
    relation_fields = {column.name for column in inspect(InstrumentTopicRelation).columns}
    assert relation_fields >= {
        "structural_role",
        "approval_state",
        "authority_version",
        "source_artifact_id",
        "source_artifact_hash",
        "approval_reference",
        "correction_sequence",
        "supersedes_authority_id",
        "superseded_by_authority_id",
        "lineage_hash",
    }
    assert {column.name for column in inspect(TopicScoreProjection).columns} >= {
        "projection_id",
        "projection_version",
        "effective_from",
        "effective_to",
        "approval_state",
        "approval_reference",
        "source_structural_role_authority_id",
        "source_structural_role_authority_version",
        "projection_lineage",
        "correction_sequence",
        "supersedes_projection_id",
        "superseded_by_projection_id",
    }
    assert {column.name for column in inspect(TopicScoreProjectionMember).columns} >= {
        "instrument_id",
        "score_importance",
        "structural_role_authority_id",
        "structural_role_authority_version",
    }


def test_approved_effective_core_resolves_and_related_resolves_but_projection_rejects_related():
    core = _authority()
    resolved = resolve_structural_role_records((core,), "topic-1", "instrument-1", AS_OF)
    assert resolved.structural_role == STRUCTURAL_ROLE_CORE
    assert resolved.read_mode == AUTHORITY_READ_CURRENT

    related = _authority(role=STRUCTURAL_ROLE_RELATED)
    related_resolution = resolve_structural_role_records(
        (related,), "topic-1", "instrument-1", AS_OF
    )
    assert related_resolution.structural_role == STRUCTURAL_ROLE_RELATED
    with pytest.raises(ScoreProjectionError, match="NOT_CORE"):
        resolve_score_projection_records(
            (_projection(),),
            "topic-1",
            AS_OF,
            _resolve_authority((related,)),
        )


@pytest.mark.parametrize(
    "record, message",
    [
        (_authority(approval_state="PROPOSED"), "not APPROVED"),
        (_authority(effective_from=date(2026, 8, 8)), "NOT_EFFECTIVE"),
        (_authority(superseded_by="authority-2"), "SUPERSEDED"),
    ],
)
def test_role_authority_fail_closed(record, message):
    with pytest.raises(StructuralRoleAuthorityError, match=message):
        resolve_structural_role_records((record,), "topic-1", "instrument-1", AS_OF)


def test_historical_role_resolution_preserves_superseded_identity():
    superseded = _authority(superseded_by="authority-2")
    resolution = resolve_structural_role_records(
        (superseded,),
        "topic-1",
        "instrument-1",
        AS_OF,
        read_mode=AUTHORITY_READ_HISTORICAL,
    )
    assert resolution.authority_id == "authority-1"
    assert resolution.is_superseded is True


def test_two_active_authorities_fail_closed():
    first = _authority()
    second = _authority(authority_id="authority-2", authority_version="roles.v2")
    with pytest.raises(StructuralRoleAuthorityError, match="CONFLICT"):
        resolve_structural_role_records(
            (first, second), "topic-1", "instrument-1", AS_OF
        )


def test_projection_accepts_only_valid_core_members_and_adapter_is_deterministic():
    authority = _authority()
    resolution = resolve_score_projection_records(
        (_projection(),),
        "topic-1",
        AS_OF,
        _resolve_authority((authority,)),
    )
    leader_set = build_governed_leader_set(resolution)
    assert leader_set.version == "projection.v1"
    assert leader_set.artifact_id == "projection-1"
    assert leader_set.leaders_for("topic-1")[0].member_id == "instrument-1"
    assert leader_set.leaders_for("topic-1")[0].importance == 1.0


@pytest.mark.parametrize(
    "projection, message",
    [
        (_projection(importance=Decimal("0.60")), "SCORE_IMPORTANCE_INVALID"),
        (_projection(source_version=""), "source_structural_role_authority_version"),
        (_projection(approval_state="PROPOSED"), "NOT_APPROVED"),
        (_projection(superseded_by="projection-row-2"), "SUPERSEDED"),
    ],
)
def test_projection_validation_fail_closed(projection, message):
    authority = _authority()
    with pytest.raises(ScoreProjectionError, match=message):
        resolve_score_projection_records(
            (projection,),
            "topic-1",
            AS_OF,
            _resolve_authority((authority,)),
        )


def test_projection_requires_exact_authority_binding_and_historical_mode_is_explicit():
    authority = _authority(superseded_by="authority-2")
    with pytest.raises(ScoreProjectionError, match="STRUCTURAL_ROLE_AUTHORITY_INVALID"):
        resolve_score_projection_records(
            (_projection(),),
            "topic-1",
            AS_OF,
            _resolve_authority((authority,)),
        )

    resolution = resolve_score_projection_records(
        (_projection(),),
        "topic-1",
        AS_OF,
        _resolve_authority((authority,)),
        read_mode=SCORE_PROJECTION_READ_HISTORICAL,
    )
    assert resolution.read_mode == SCORE_PROJECTION_READ_HISTORICAL


def test_missing_topic_projection_is_bounded_to_that_topic():
    authority = _authority()
    resolver = _resolve_authority((authority,))
    ready = resolve_score_projection_records(
        (_projection(),), "topic-1", AS_OF, resolver, read_mode=SCORE_PROJECTION_READ_CURRENT
    )
    assert ready.topic_id == "topic-1"
    with pytest.raises(ScoreProjectionError, match="SCORE_PROJECTION_MISSING"):
        resolve_score_projection_records((), "topic-2", AS_OF, resolver)
