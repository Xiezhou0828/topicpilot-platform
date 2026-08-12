"""Generic persistence primitives shared by V2 repositories."""

from typing import Protocol

from sqlalchemy.orm import Session


class ReadRepository[T](Protocol):
    def get(self, identity): ...


class WriteRepository[T](ReadRepository[T], Protocol):
    def add(self, entity: T) -> T: ...


class SqlRepository[T]:
    def __init__(self, session: Session, model: type[T]):
        self.session, self.model = session, model

    def get(self, identity):
        return self.session.get(self.model, identity)

    def add(self, entity):
        self.session.add(entity)
        return entity


class RepositoryRegistry:
    def __init__(self, session: Session):
        self.session = session
        self._items = {}

    def for_model(self, model):
        return self._items.setdefault(
            model, SqlRepository(self.session, model)
        )
