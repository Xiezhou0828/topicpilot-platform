from datetime import date

from sqlalchemy import inspect

from topicpilot_api.orm import Topic, TopicHierarchy


def test_topic_domain_models_define_expected_schema():
    assert Topic.__tablename__ == "topics"
    assert TopicHierarchy.__tablename__ == "topic_hierarchy"
    assert {column.name for column in inspect(Topic).columns} >= {
        "slug", "name", "description", "status", "dictionary_version",
        "valid_from", "valid_to", "display_metadata",
    }
    assert {column.name for column in inspect(TopicHierarchy).columns} >= {
        "parent_topic_id", "child_topic_id", "relationship_type", "hierarchy_version",
        "valid_from", "valid_to", "display_order",
    }


def test_topic_hierarchy_preserves_parent_child_relationships_and_history():
    root = Topic(slug="energy", name="Energy", status="ACTIVE", dictionary_version="v1")
    child = Topic(slug="renewables", name="Renewables", status="ACTIVE", dictionary_version="v1")
    edge = TopicHierarchy(
        parent=root,
        child=child,
        hierarchy_version="v1",
        valid_from=date(2026, 1, 1),
        display_order=1,
    )

    assert edge.parent is root
    assert edge.child is child
    assert root.child_relationships == [edge]
    assert child.parent_relationships == [edge]
    assert edge.valid_to is None
