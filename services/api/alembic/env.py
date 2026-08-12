from __future__ import annotations

from logging.config import fileConfig

from sqlalchemy import Column, MetaData, String, Table, engine_from_config, pool, text

from alembic import context
from topicpilot_api import models  # noqa: F401
from topicpilot_api.config import get_settings
from topicpilot_api.database import Base
from topicpilot_api.orm import models as v2_models  # noqa: F401
from topicpilot_api.orm.base import Base as V2Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

settings = get_settings()
migration_database_url = settings.migration_database_url or settings.database_url
config.set_main_option("sqlalchemy.url", migration_database_url.replace("%", "%%"))
# Keep the two declarative bases separate: compatibility tables remain owned by
# the legacy/public base while V2 tables are owned by topicpilot. Alembic accepts
# multiple metadata collections and therefore can detect drift in both domains.
target_metadata = [Base.metadata, V2Base.metadata]


def _ensure_version_table(connection) -> None:
    """Create Alembic's version table with room for descriptive revision IDs.

    Alembic's default version_num length is 32 characters. This repository uses
    descriptive revision IDs that can be longer, so the table must exist with
    the repository-wide length before Alembic starts applying revisions.
    """
    version_metadata = MetaData()
    Table(
        "alembic_version",
        version_metadata,
        Column("version_num", String(255), primary_key=True, nullable=False),
    ).create(connection, checkfirst=True)
    # Also repair databases created before this foundation safeguard existed.
    if connection.dialect.name == "postgresql":
        connection.execute(
            text("ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(255)")
        )
        connection.commit()


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        include_schemas=True,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        _ensure_version_table(connection)
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
