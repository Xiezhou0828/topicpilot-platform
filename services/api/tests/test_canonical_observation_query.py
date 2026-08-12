from datetime import date
from unittest.mock import Mock
from uuid import uuid4

import pytest
from sqlalchemy.dialects import postgresql

from topicpilot_api.repositories.canonical_observations import (
    read_approved_price_observations_for_as_of,
)


def test_as_of_price_query_requires_explicit_instrument_boundary():
    with pytest.raises(ValueError, match="instrument_ids must be non-empty"):
        read_approved_price_observations_for_as_of(
            Mock(),
            (),
            as_of=date(2026, 8, 7),
            timezone_name="Asia/Taipei",
            session_code="REGULAR",
            source_id=uuid4(),
        )


def test_as_of_price_query_binds_source_session_and_exact_day_without_fallback():
    session = Mock()
    session.scalars.return_value = []
    source_id = uuid4()

    result = read_approved_price_observations_for_as_of(
        session,
        (uuid4(),),
        as_of=date(2026, 8, 7),
        timezone_name="Asia/Taipei",
        session_code="REGULAR",
        source_id=source_id,
    )

    assert result == []
    statement = session.scalars.call_args.args[0]
    sql = str(statement.compile(dialect=postgresql.dialect()))
    assert "canonical_observations" in sql
    assert "canonical_price_observations" in sql
    assert "session_code" in sql
    assert "source_id" in sql
    assert "topic_snapshots" not in sql
