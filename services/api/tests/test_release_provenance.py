from fastapi.testclient import TestClient

from topicpilot_api.main import create_app
from topicpilot_api.release_provenance import runtime_git_sha


def test_runtime_git_sha_prefers_valid_render_commit(monkeypatch):
    monkeypatch.setenv("RENDER_GIT_COMMIT", "A" * 40)
    monkeypatch.setenv("GIT_SHA", "B" * 40)

    assert runtime_git_sha() == "a" * 40


def test_runtime_git_sha_falls_back_to_valid_git_sha(monkeypatch):
    monkeypatch.delenv("RENDER_GIT_COMMIT", raising=False)
    monkeypatch.setenv("GIT_SHA", "B" * 40)

    assert runtime_git_sha() == "b" * 40


def test_runtime_git_sha_fails_closed_for_missing_or_malformed_values(monkeypatch):
    monkeypatch.delenv("RENDER_GIT_COMMIT", raising=False)
    monkeypatch.delenv("GIT_SHA", raising=False)
    assert runtime_git_sha() == "UNKNOWN"

    secret_value = "not-a-runtime-secret"
    monkeypatch.setenv("RENDER_GIT_COMMIT", secret_value)
    monkeypatch.setenv("GIT_SHA", "C" * 40)
    assert runtime_git_sha() == "UNKNOWN"
    response = TestClient(create_app()).get("/healthz")
    assert response.json() == {"status": "ok", "gitSha": "UNKNOWN"}
    assert secret_value not in response.text
