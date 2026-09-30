from topicpilot_api.config import Settings
from topicpilot_api.live.config import LiveRuntimeConfig


def test_cors_origins_accepts_single_origin(monkeypatch) -> None:
    monkeypatch.setenv("TOPICPILOT_CORS_ORIGINS", "http://localhost:3000")

    settings = Settings(_env_file=None)

    assert settings.cors_origins == ("http://localhost:3000",)


def test_cors_origins_accepts_comma_separated_origins(monkeypatch) -> None:
    monkeypatch.setenv(
        "TOPICPILOT_CORS_ORIGINS",
        "https://demo.example, https://portfolio.example",
    )

    settings = Settings(_env_file=None)

    assert settings.cors_origins == (
        "https://demo.example",
        "https://portfolio.example",
    )


def test_cors_origins_accepts_json_array(monkeypatch) -> None:
    monkeypatch.setenv(
        "TOPICPILOT_CORS_ORIGINS",
        '["https://demo.example", "https://portfolio.example"]',
    )

    settings = Settings(_env_file=None)

    assert settings.cors_origins == (
        "https://demo.example",
        "https://portfolio.example",
    )


def test_migration_database_url_is_separate_from_runtime_database_url(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://pooled.example/app")
    monkeypatch.setenv("MIGRATION_DATABASE_URL", "postgresql+psycopg://direct.example/app")

    settings = Settings(_env_file=None)

    assert settings.database_url.endswith("pooled.example/app")
    assert settings.migration_database_url.endswith("direct.example/app")


def test_status_resolution_budget_is_separate_and_environment_configurable(monkeypatch) -> None:
    monkeypatch.setenv("TOPICPILOT_STATUS_RESOLUTION_MAX_ATTEMPTS", "4")
    monkeypatch.setenv("TOPICPILOT_STATUS_RESOLUTION_MAX_TOTAL_WAIT_SECONDS", "75")
    monkeypatch.setenv("TOPICPILOT_STATUS_RESOLUTION_BACKOFF_SECONDS", "15")

    config = LiveRuntimeConfig.from_environment()

    assert config.status_resolution_max_attempts == 4
    assert config.status_resolution_max_total_wait_seconds == 75.0
    assert config.status_resolution_backoff_seconds == 15.0
    assert config.history_readiness_max_attempts != 4 or (
        config.history_readiness_max_total_wait_seconds
        != config.status_resolution_max_total_wait_seconds
    )
    assert config.as_dict()["statusResolutionMaxAttempts"] == 4
