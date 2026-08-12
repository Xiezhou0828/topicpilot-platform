from __future__ import annotations

from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import Engine, MetaData, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from topicpilot_api.config import get_settings


class Base(DeclarativeBase):
    # Compatibility/demo ORM owns the legacy public schema explicitly. V2 ORM
    # models use their separate Base with schema="topicpilot".
    metadata = MetaData(schema="public")


@lru_cache
def get_engine() -> Engine:
    url = get_settings().database_url
    return create_engine(
        url,
        pool_pre_ping=True,
        pool_recycle=1800,
    )


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), expire_on_commit=False, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    with get_session_factory()() as session:
        yield session
