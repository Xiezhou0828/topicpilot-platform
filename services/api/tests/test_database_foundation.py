from __future__ import annotations

import configparser
from pathlib import Path

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory

API_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = API_ROOT.parents[1]


def test_alembic_has_one_linear_head_and_no_create_all() -> None:
    config = Config(str(API_ROOT / "alembic.ini"))
    scripts = ScriptDirectory.from_config(config)

    heads = list(scripts.get_heads())
    assert len(heads) == 1
    assert scripts.get_current_head() == heads[0]
    assert all(
        "create_all" not in path.read_text(encoding="utf-8")
        for path in (API_ROOT / "alembic").rglob("*.py")
    )


def test_alembic_migration_contract() -> None:
    config = Config(str(API_ROOT / "alembic.ini"))
    scripts = ScriptDirectory.from_config(config)

    revisions = list(scripts.walk_revisions(base="base", head="heads"))
    assert revisions
    assert all(revision.revision for revision in revisions)
    assert all(revision.module.upgrade and revision.module.downgrade for revision in revisions)


def test_alembic_configuration_delegates_database_url_to_environment() -> None:
    parser = configparser.ConfigParser()
    parser.read(API_ROOT / "alembic.ini", encoding="utf-8")

    assert parser["alembic"]["sqlalchemy.url"] == ""
    env_source = (API_ROOT / "alembic" / "env.py").read_text(encoding="utf-8")
    assert "get_settings()" in env_source
    assert "migration_database_url" in env_source
    assert "database_url" in env_source
    assert 'String(255)' in env_source
    assert '_ensure_version_table(connection)' in env_source
    assert 'ALTER COLUMN version_num TYPE VARCHAR(255)' in env_source


def test_reproducible_local_setup_has_ignored_env_and_compose_database() -> None:
    gitignore = (REPOSITORY_ROOT / ".gitignore").read_text(encoding="utf-8")
    compose = (REPOSITORY_ROOT / "compose.yaml").read_text(encoding="utf-8")

    assert ".env" in gitignore
    assert "postgres:16-alpine" in compose
    assert "alembic upgrade head" in compose


@pytest.mark.postgres
def test_migration_state_matches_head(postgres_engine) -> None:
    from sqlalchemy import text

    config = Config(str(API_ROOT / "alembic.ini"))
    scripts = ScriptDirectory.from_config(config)
    heads = list(scripts.get_heads())
    assert len(heads) == 1

    with postgres_engine.connect() as connection:
        revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()

    assert revision == heads[0]
