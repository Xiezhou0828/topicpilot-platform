from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy.orm import Session, sessionmaker

from .repositories import RepositoryRegistry


class PersistenceError(RuntimeError):
    pass


class UnitOfWork:
    def __init__(self, session: Session):
        self.session = session
        self.repositories = RepositoryRegistry(session)

    def commit(self):
        try:
            self.session.commit()
        except Exception as exc:
            self.session.rollback()
            raise PersistenceError("transaction commit failed") from exc

    def rollback(self):
        self.session.rollback()

    def __enter__(self):
        return self

    def __exit__(self, typ, value, tb):
        if typ:
            self.rollback()
        else:
            self.commit()
        self.session.close()


@contextmanager
def unit_of_work(factory: sessionmaker[Session]) -> Iterator[UnitOfWork]:
    with UnitOfWork(factory()) as uow:
        yield uow


def runtime_persistence(factory: sessionmaker[Session]):
    """Persistence boundary for an already-computed runtime result; no domain logic."""
    return unit_of_work(factory)
