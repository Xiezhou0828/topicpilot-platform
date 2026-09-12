from __future__ import annotations

from copy import deepcopy
from types import SimpleNamespace

import pytest

import topicpilot_api.topic_authority_activation as authority
from topicpilot_api.topic_authority_activation import (
    TopicAuthorityActivationError,
    activate_topic_authority,
    artifact_hash,
    parse_activation_artifact,
)

PARENT_ID = "10000000-0000-0000-0000-000000000001"
LEAF_ID = "20000000-0000-0000-0000-000000000001"


def _payload() -> dict:
    payload = {
        "schemaVersion": "topic-authority-activation.v1",
        "activationVersion": "topic-authority-test.v1",
        "artifactSha256": "",
        "sourceMasterSha256": "a" * 64,
        "sourceRevision": "b" * 40,
        "targetEnvironment": "production",
        "targetDatabase": "topicpilot-production",
        "approvalReference": "OWNER-TEST",
        "effectiveDate": "2026-09-11",
        "expectedParentCount": 1,
        "expectedLeafCount": 1,
        "topics": [
            {
                "topicId": PARENT_ID,
                "slug": "parent",
                "name": "Parent",
                "level": "PARENT",
                "status": "ENABLED",
                "action": "PRESERVE",
                "expectedCurrentSlug": "parent",
            },
            {
                "topicId": LEAF_ID,
                "slug": "leaf",
                "name": "Leaf",
                "level": "LEAF",
                "status": "ENABLED",
                "action": "PRESERVE",
                "expectedCurrentSlug": "leaf",
            },
        ],
        "hierarchy": [{"parentTopicId": PARENT_ID, "childTopicId": LEAF_ID}],
        "lifecycleScope": [
            {
                "researchIdentity": "Leaf",
                "canonicalTopicId": LEAF_ID,
                "mappingReason": "PRESERVED",
                "status": "RESOLVED",
            }
        ],
    }
    payload["artifactSha256"] = artifact_hash(payload)
    return payload


def _artifact(change=None):
    payload = deepcopy(_payload())
    if change:
        change(payload)
        payload["artifactSha256"] = artifact_hash(payload)
    return parse_activation_artifact(payload)


class _Transaction:
    def __init__(self, session):
        self.session = session

    def __enter__(self):
        self.session.in_tx = True
        return self

    def __exit__(self, exc_type, _exc, _tb):
        self.session.in_tx = False
        if exc_type:
            self.session.transaction_rollbacks += 1
        else:
            self.session.transaction_commits += 1
        return False


class _Scalar:
    def __init__(self, value):
        self.value = value

    def scalar_one(self):
        return self.value


class FakeSession:
    def __init__(self, database="topicpilot-production"):
        self.bind = SimpleNamespace(dialect=SimpleNamespace(name="postgresql"))
        self.database = database
        self.in_tx = False
        self.rollback_calls = 0
        self.transaction_rollbacks = 0
        self.transaction_commits = 0
        self.added = []

    def execute(self, _statement):
        self.in_tx = True
        return _Scalar(self.database)

    def in_transaction(self):
        return self.in_tx

    def rollback(self):
        self.rollback_calls += 1
        self.in_tx = False

    def begin(self):
        return _Transaction(self)

    def add(self, row):
        self.added.append(row)

    def flush(self):
        return None

    def scalar(self, _statement):
        return None


@pytest.fixture
def mocked_database(monkeypatch):
    readback = {
        "activeParentCount": 1,
        "activeLeafCount": 1,
        "lifecycleScopeCount": 1,
        "readbackSha256": "c" * 64,
    }
    calls = {"preflight": 0, "topics": 0, "hierarchy": 0, "readback": 0}
    monkeypatch.setattr(authority, "_existing_activation", lambda *_: None)
    monkeypatch.setattr(
        authority,
        "_preflight_database",
        lambda *_: calls.__setitem__("preflight", calls["preflight"] + 1),
    )
    monkeypatch.setattr(
        authority,
        "_apply_topics",
        lambda *_: calls.__setitem__("topics", calls["topics"] + 1),
    )
    monkeypatch.setattr(
        authority,
        "_apply_hierarchy",
        lambda *_: calls.__setitem__("hierarchy", calls["hierarchy"] + 1),
    )

    def readback_fn(*_args):
        calls["readback"] += 1
        return readback

    monkeypatch.setattr(authority, "_readback", readback_fn)
    return calls, readback


def _activate(session, artifact, **overrides):
    kwargs = {
        "dry_run": False,
        "runtime_environment": "production",
        "expected_database": "topicpilot-production",
        "runtime_revision": "d" * 40,
        "operator_id": "owner",
        "confirmation": f"ACTIVATE:{artifact.activation_version}:{artifact.artifact_sha256}",
    }
    kwargs.update(overrides)
    return activate_topic_authority(session, artifact, **kwargs)


def test_dry_run_has_zero_mutation(mocked_database):
    calls, _ = mocked_database
    artifact = _artifact()
    session = FakeSession()
    result = _activate(session, artifact, dry_run=True, confirmation=None)
    assert result.operation == "DRY_RUN_PASS"
    assert calls == {"preflight": 1, "topics": 0, "hierarchy": 0, "readback": 0}
    assert session.added == []
    assert session.transaction_commits == 0


def test_wrong_environment_or_database_is_rejected(mocked_database):
    artifact = _artifact()
    with pytest.raises(TopicAuthorityActivationError, match="environment"):
        _activate(FakeSession(), artifact, runtime_environment="local")
    with pytest.raises(TopicAuthorityActivationError, match="database identity"):
        _activate(FakeSession(database="topicpilot-local"), artifact)


def test_duplicate_mapping_is_rejected():
    def duplicate(payload):
        payload["lifecycleScope"].append(dict(payload["lifecycleScope"][0]))

    with pytest.raises(TopicAuthorityActivationError, match="duplicate Lifecycle"):
        _artifact(duplicate)


def test_obsolete_identity_is_rejected_from_scope():
    def obsolete(payload):
        payload["topics"][1]["status"] = "RETIRED"

    with pytest.raises(TopicAuthorityActivationError, match="inactive or unknown"):
        _artifact(obsolete)


def test_parent_is_rejected_from_leaf_scope():
    def parent(payload):
        payload["lifecycleScope"][0]["canonicalTopicId"] = PARENT_ID

    with pytest.raises(TopicAuthorityActivationError, match="Parent cannot"):
        _artifact(parent)


def test_transaction_rolls_back_on_write_failure(monkeypatch, mocked_database):
    session = FakeSession()
    artifact = _artifact()
    monkeypatch.setattr(
        authority, "_apply_topics", lambda *_: (_ for _ in ()).throw(ValueError("write"))
    )
    with pytest.raises(ValueError, match="write"):
        _activate(session, artifact)
    assert session.transaction_rollbacks == 1
    assert session.transaction_commits == 0


def test_valid_activation_succeeds(mocked_database):
    calls, readback = mocked_database
    session = FakeSession()
    result = _activate(session, _artifact())
    assert result.operation == "ACTIVATED"
    assert result.readback_sha256 == readback["readbackSha256"]
    assert calls == {"preflight": 1, "topics": 1, "hierarchy": 1, "readback": 1}
    assert session.transaction_commits == 1
    assert len(session.added) == 1


def test_same_version_same_content_is_idempotent(monkeypatch, mocked_database):
    _, readback = mocked_database
    artifact = _artifact()
    existing = SimpleNamespace(
        artifact_sha256=artifact.artifact_sha256,
        readback_sha256=readback["readbackSha256"],
    )
    monkeypatch.setattr(authority, "_existing_activation", lambda *_: existing)
    session = FakeSession()
    result = _activate(session, artifact)
    assert result.operation == "NOOP"
    assert session.added == []


def test_same_version_different_content_fails_closed(monkeypatch, mocked_database):
    artifact = _artifact()
    monkeypatch.setattr(
        authority,
        "_existing_activation",
        lambda *_: SimpleNamespace(artifact_sha256="d" * 64),
    )
    with pytest.raises(TopicAuthorityActivationError, match="different content"):
        _activate(FakeSession(), artifact)


def test_post_activation_readback_mismatch_rolls_back(monkeypatch, mocked_database):
    artifact = _artifact()
    session = FakeSession()
    monkeypatch.setattr(
        authority,
        "_readback",
        lambda *_: (_ for _ in ()).throw(
            TopicAuthorityActivationError("post-activation readback scope mismatch")
        ),
    )
    with pytest.raises(TopicAuthorityActivationError, match="readback scope mismatch"):
        _activate(session, artifact)
    assert session.transaction_rollbacks == 1


def test_create_requires_explicit_artifact_authority():
    def create_without_authority(payload):
        payload["topics"][1]["action"] = "CREATE"
        payload["topics"][1].pop("expectedCurrentSlug")

    with pytest.raises(TopicAuthorityActivationError, match="creation lacks"):
        _artifact(create_without_authority)


def test_artifact_content_hash_is_mandatory():
    payload = _payload()
    payload["topics"][1]["name"] = "Changed"
    with pytest.raises(TopicAuthorityActivationError, match="content hash mismatch"):
        parse_activation_artifact(payload)
