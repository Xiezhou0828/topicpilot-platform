from __future__ import annotations

from datetime import date

from topicpilot_api.production_read_model import _strength_read
from topicpilot_api.schemas import TopicOwnerSeededV0Read


def test_persisted_strength_serializes_snapshot_date_for_topic_contract(monkeypatch):
    monkeypatch.setattr(
        "topicpilot_api.production_read_model.build_topic_strength_lifecycle_read",
        lambda *_args, **_kwargs: {
            "ownerSeededV0": {
                "status": "WAITING_FOR_CANONICAL_ACTIVATION",
                "policyId": "policy",
                "policyVersion": "v1",
                "policyHash": "hash",
                "implementationSha": None,
                "asOfDate": None,
                "formalDailyGrade": None,
                "absolute": {"score": None, "grade": None},
                "relative": {"score": None, "grade": None},
                "lifecycle": {},
                "observationFlags": [],
                "observationFlagCopy": {},
                "qualityFlags": {},
                "diagnosticOnly": True,
            },
            "forwardObservation": {},
        },
    )

    result = _strength_read(
        object(),
        {
            "slug": "topic-a",
            "snapshot_date": date(2026, 10, 7),
            "formal_strength_components": {
                "absolute": {"strength": 10, "grade": "B"},
                "relative": {"strength": 8, "grade": "C"},
                "formalDailyGrade": "B",
                "qualityFlags": {},
            },
            "formal_strength_publication_status": "PUBLISHED",
        },
        None,
    )

    owner = TopicOwnerSeededV0Read.model_validate(result["ownerSeededV0"])
    assert owner.as_of_date == "2026-10-07"
