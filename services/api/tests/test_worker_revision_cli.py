import json

from topicpilot_api.worker_revision_cli import main


def test_worker_revision_readback_returns_exact_runtime_sha(monkeypatch, capsys):
    monkeypatch.setenv("RENDER_GIT_COMMIT", "A" * 40)

    assert main(["--json"]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload == {
        "readbackStatus": "READY",
        "runtimeGitSha": "a" * 40,
        "source": "RENDER_GIT_COMMIT_OR_GIT_SHA",
    }


def test_worker_revision_readback_fails_closed_without_runtime_sha(monkeypatch, capsys):
    monkeypatch.delenv("RENDER_GIT_COMMIT", raising=False)
    monkeypatch.delenv("GIT_SHA", raising=False)

    assert main(["--json"]) == 1

    payload = json.loads(capsys.readouterr().out)
    assert payload["readbackStatus"] == "UNVERIFIED"
    assert payload["runtimeGitSha"] == "UNKNOWN"
