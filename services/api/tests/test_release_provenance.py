from topicpilot_api.release_provenance import runtime_git_sha


def test_runtime_git_sha_prefers_valid_render_revision(monkeypatch):
    monkeypatch.setenv("GIT_SHA", "b" * 40)
    monkeypatch.setenv("RENDER_GIT_COMMIT", "A" * 40)

    assert runtime_git_sha() == "a" * 40


def test_runtime_git_sha_fails_closed_for_untrusted_values(monkeypatch):
    monkeypatch.delenv("RENDER_GIT_COMMIT", raising=False)
    monkeypatch.setenv("GIT_SHA", "not-a-sha")

    assert runtime_git_sha() == "UNKNOWN"
