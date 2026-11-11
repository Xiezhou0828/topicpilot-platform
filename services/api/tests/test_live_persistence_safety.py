from __future__ import annotations

from datetime import date
from types import SimpleNamespace

import pytest
from sqlalchemy.exc import DBAPIError

from topicpilot_api.live.config import LiveRuntimeConfig
from topicpilot_api.live.persistence import LiveRepository
from topicpilot_api.live.post_close import PostClosePreconditionError, PostCloseUpdater


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


class _LockTimeoutOriginal(Exception):
    sqlstate = "55P03"


class _ClaimSettingsResult:
    def mappings(self):
        return self

    def one(self):
        return {"lock_timeout": "0", "statement_timeout": "0"}


class _ClaimSession:
    def __init__(self, *, timeout_lock: bool = False):
        self.timeout_lock = timeout_lock
        self.executed = []
        self.rollback_calls = 0
        self.is_active = True

    def get_bind(self):
        return SimpleNamespace(dialect=SimpleNamespace(name="postgresql"))

    def execute(self, statement, parameters=None):
        sql = str(statement)
        self.executed.append((sql, parameters))
        if "current_setting" in sql:
            return _ClaimSettingsResult()
        if "pg_advisory_xact_lock" in sql and self.timeout_lock:
            raise DBAPIError(sql, parameters, _LockTimeoutOriginal())
        return SimpleNamespace()

    def rollback(self):
        self.rollback_calls += 1


def _post_close_updater(session, config):
    updater = PostCloseUpdater.__new__(PostCloseUpdater)
    updater.session = session
    updater.config = config
    return updater


def test_session_claim_lock_uses_bounded_postgres_timeouts_once():
    session = _ClaimSession()
    config = LiveRuntimeConfig(
        session_claim_lock_timeout_seconds=4.5,
        session_claim_statement_timeout_seconds=7.5,
    )

    _post_close_updater(session, config)._acquire_session_claim_lock(
        date(2026, 10, 13)
    )

    settings = [call for call in session.executed if "set_config" in call[0]]
    locks = [call for call in session.executed if "pg_advisory_xact_lock" in call[0]]
    assert settings[0][1] == {"lock_timeout": "4500ms", "statement_timeout": "7500ms"}
    assert len(locks) == 1
    assert session.rollback_calls == 0


def test_session_claim_lock_timeout_is_a_concurrency_precondition():
    session = _ClaimSession(timeout_lock=True)
    updater = _post_close_updater(session, LiveRuntimeConfig())

    with pytest.raises(PostClosePreconditionError, match="POST_CLOSE_RUN_IN_PROGRESS"):
        updater._acquire_session_claim_lock(date(2026, 10, 13))

    assert session.rollback_calls == 1


def test_session_claim_timeouts_are_environment_configurable(monkeypatch):
    monkeypatch.setenv("TOPICPILOT_LIVE_SESSION_CLAIM_LOCK_TIMEOUT_SECONDS", "6.5")
    monkeypatch.setenv("TOPICPILOT_LIVE_SESSION_CLAIM_STATEMENT_TIMEOUT_SECONDS", "7.5")

    config = LiveRuntimeConfig.from_environment()

    assert config.session_claim_lock_timeout_seconds == 6.5
    assert config.session_claim_statement_timeout_seconds == 7.5
    assert config.as_dict()["sessionClaimLockTimeoutSeconds"] == 6.5
    assert config.as_dict()["sessionClaimStatementTimeoutSeconds"] == 7.5
