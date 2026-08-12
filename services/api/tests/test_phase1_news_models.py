from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from topicpilot_api.models import NewsArticle, NewsStockRelation, NewsTopicRelation, Stock, Topic


def test_phase1_news_relations_are_unique_and_fk_backed(db_session) -> None:
    suffix = uuid4().hex[:8]
    stock = Stock(code=f"DN{suffix}", name="Synthetic News Co", market="DEMO")
    topic = Topic(
        slug=f"synthetic-news-{suffix}",
        name="Synthetic News",
        topic_type="APPLICATION",
    )
    db_session.add_all([stock, topic])
    db_session.flush()

    article = NewsArticle(
        article_key=f"demo-news-{suffix}",
        source_name="Synthetic Wire",
        title="Synthetic article for migration testing",
        published_at=datetime(2026, 7, 31, 8, 0, tzinfo=UTC),
        classification="PUBLIC_SYNTHETIC",
    )
    db_session.add(article)
    db_session.flush()
    db_session.add_all(
        [
            NewsStockRelation(
                news_article_id=article.id,
                stock_id=stock.id,
                relation_type="MENTION",
                evidence_summary="Synthetic relation",
            ),
            NewsTopicRelation(
                news_article_id=article.id,
                topic_id=topic.id,
                relation_type="ABOUT",
                relevance_score=0.8,
            ),
        ]
    )
    db_session.commit()

    assert db_session.scalar(select(NewsArticle.article_key)) == article.article_key
    assert db_session.scalar(select(NewsStockRelation.relation_type)) == "MENTION"
    assert db_session.scalar(select(NewsTopicRelation.relation_type)) == "ABOUT"

    duplicate = NewsStockRelation(
        news_article_id=article.id,
        stock_id=stock.id,
        relation_type="MENTION",
    )
    db_session.add(duplicate)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
