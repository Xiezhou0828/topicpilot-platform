from __future__ import annotations

from types import SimpleNamespace

from topicpilot_api.live.config import LiveRuntimeConfig
from topicpilot_api.live.persistence import LiveRepository


class _Result:
    def mappings(self):
        return self

    def one(self):
        return {
            "lock_timeout": "0",
            "statement_timeout": "0",
        }


class _Session:
    def __init__(self):
        self.new = {object()}
        self.dirty = set()
        self.executed = []
        self.flush_count = 0

    def get_bind(self):
        return SimpleNamespace(dialect=SimpleNamespace(name="postgresql"))

    def execute(self, statement, parameters=None):
        self.executed.append((str(statement), parameters))
        if "current_setting" in str(statement):
            return _Result()
        return None

    def flush(self):
        self.flush_count += 1
        self.new.clear()


def test_tracking_refresh_timeout_is_scoped_to_each_flush():
    session = _Session()
    repository = LiveRepository(session, LiveRuntimeConfig())

    repository._flush_tracking_batch()

    assert session.flush_count == 1
    assert len(session.executed) == 3
    set_config_calls = [call for call in session.executed if "set_config" in call[0]]
    assert len(set_config_calls) == 2
    assert set_config_calls[0][1] == {
        "lock_timeout": "30000ms",
        "statement_timeout": "120000ms",
    }
    assert set_config_calls[1][1] == {
        "lock_timeout": "0",
        "statement_timeout": "0",
    }


def test_tracking_refresh_safety_settings_are_environment_configurable(monkeypatch):
    monkeypatch.setenv("TOPICPILOT_LIVE_TRACKING_REFRESH_BATCH_SIZE", "17")
    monkeypatch.setenv("TOPICPILOT_LIVE_TRACKING_REFRESH_LOCK_TIMEOUT_SECONDS", "4.5")
    monkeypatch.setenv("TOPICPILOT_LIVE_TRACKING_REFRESH_STATEMENT_TIMEOUT_SECONDS", "45")

    config = LiveRuntimeConfig.from_environment()

    assert config.tracking_refresh_batch_size == 17
    assert config.tracking_refresh_lock_timeout_seconds == 4.5
    assert config.tracking_refresh_statement_timeout_seconds == 45.0
