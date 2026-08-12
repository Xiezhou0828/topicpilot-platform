"""Add Phase 1 news entities and relation tables.

Revision ID: 0002_phase1_news_entities
Revises: 0001
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0002_phase1_news_entities"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "news_articles",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("article_key", sa.String(length=200), nullable=False),
        sa.Column("source_name", sa.String(length=160), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "retrieved_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("language", sa.String(length=16), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=True),
        sa.Column("classification", sa.String(length=64), nullable=False),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.CheckConstraint(
            "classification IN ('PUBLIC_SYNTHETIC', 'PRIVATE_FORMAL')",
            name="ck_news_article_classification",
        ),
        sa.UniqueConstraint("article_key", name="uq_news_article_key"),
    )
    op.create_index(
        "ix_news_articles_published_at", "news_articles", ["published_at"]
    )
    op.create_index(
        "ix_news_articles_source_name_published_at",
        "news_articles",
        ["source_name", "published_at"],
    )

    op.create_table(
        "news_stock_relations",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column(
            "news_article_id",
            sa.BigInteger(),
            sa.ForeignKey("news_articles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "stock_id",
            sa.BigInteger(),
            sa.ForeignKey("stocks.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("relation_type", sa.String(length=32), nullable=False),
        sa.Column("relevance_score", sa.Numeric(12, 4), nullable=True),
        sa.Column("evidence_summary", sa.Text(), nullable=True),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.UniqueConstraint(
            "news_article_id",
            "stock_id",
            "relation_type",
            name="uq_news_stock_relation",
        ),
    )
    op.create_index(
        "ix_news_stock_relations_stock_article",
        "news_stock_relations",
        ["stock_id", "news_article_id"],
    )

    op.create_table(
        "news_topic_relations",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column(
            "news_article_id",
            sa.BigInteger(),
            sa.ForeignKey("news_articles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "topic_id",
            sa.BigInteger(),
            sa.ForeignKey("topics.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("relation_type", sa.String(length=32), nullable=False),
        sa.Column("relevance_score", sa.Numeric(12, 4), nullable=True),
        sa.Column("evidence_summary", sa.Text(), nullable=True),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.UniqueConstraint(
            "news_article_id",
            "topic_id",
            "relation_type",
            name="uq_news_topic_relation",
        ),
    )
    op.create_index(
        "ix_news_topic_relations_topic_article",
        "news_topic_relations",
        ["topic_id", "news_article_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_news_topic_relations_topic_article", table_name="news_topic_relations"
    )
    op.drop_table("news_topic_relations")
    op.drop_index(
        "ix_news_stock_relations_stock_article", table_name="news_stock_relations"
    )
    op.drop_table("news_stock_relations")
    op.drop_index(
        "ix_news_articles_source_name_published_at", table_name="news_articles"
    )
    op.drop_index("ix_news_articles_published_at", table_name="news_articles")
    op.drop_table("news_articles")
