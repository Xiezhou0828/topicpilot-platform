from topicpilot_api.config import Settings


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
