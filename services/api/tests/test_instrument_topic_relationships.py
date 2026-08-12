from datetime import date
from sqlalchemy import inspect
from topicpilot_api.orm import Instrument, InstrumentTopicRelation, Market, Topic

def test_instrument_topic_relation_schema_and_relationships():
    assert InstrumentTopicRelation.__tablename__ == "instrument_topic_relations"
    assert {c.name for c in inspect(InstrumentTopicRelation).columns} >= {"instrument_id", "topic_id", "relation_type", "relation_version", "valid_from", "valid_to", "relationship_metadata"}
    market = Market(code="TSE", name="Tokyo Stock Exchange", timezone="Asia/Tokyo")
    instrument = Instrument(market=market, instrument_code="JP0000000001", instrument_type="EQUITY")
    topic = Topic(slug="energy", name="Energy", status="ACTIVE")
    relation = InstrumentTopicRelation(instrument=instrument, topic=topic, relation_type="ASSOCIATED", relation_version="v1", valid_from=date(2026, 1, 1), relationship_metadata={"basis": "governed_fixture"})
    assert relation.instrument is instrument and relation.topic is topic
    assert instrument.topic_relationships == [relation] and topic.instrument_relationships == [relation]
