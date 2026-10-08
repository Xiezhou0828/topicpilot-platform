"""Purge the eight retired Topic identities superseded by the 132-topic authority.

This is an owner-authorized, one-time Production cleanup.  It is deliberately
guarded by ``TOPICPILOT_ALLOW_RETIRED_TOPIC_PURGE=1`` so a normal API startup
or an unrelated migration run cannot perform the destructive operation.
"""

from __future__ import annotations

import os

import sqlalchemy as sa
from alembic import op

revision = "0050_task_purge_retired_topics"
down_revision = "0049_task_daily_formal_publication_receipt"
branch_labels = None
depends_on = None

TARGET_SLUGS = (
    "PCB",
    "其他建設",
    "其他晶圓材料",
    "其他自動化",
    "其他資安",
    "其他高速互連",
    "大型金融權值",
    "特殊金屬材料",
)
EXPECTED_TOPIC_TOTAL = 140
EXPECTED_RETIRED_TOTAL = 8
EXPECTED_ACTIVE_TOTAL = 132


def _execute(connection, statement: str, **parameters: object) -> None:
    connection.execute(sa.text(statement), parameters)


def upgrade() -> None:
    if os.environ.get("TOPICPILOT_ALLOW_RETIRED_TOPIC_PURGE") != "1":
        raise RuntimeError(
            "0050 is a destructive owner-authorized cleanup; set "
            "TOPICPILOT_ALLOW_RETIRED_TOPIC_PURGE=1 to execute it"
        )

    connection = op.get_bind()

    _execute(
        connection,
        """
        CREATE TEMP TABLE _topic_purge_slugs (
            slug text PRIMARY KEY
        ) ON COMMIT DROP
        """,
    )
    connection.execute(
        sa.text("INSERT INTO _topic_purge_slugs (slug) VALUES (:slug)"),
        [{"slug": slug} for slug in TARGET_SLUGS],
    )

    _execute(
        connection,
        """
        CREATE TEMP TABLE _topic_purge_ids ON COMMIT DROP AS
        SELECT t.id, t.slug
        FROM topicpilot.topics AS t
        JOIN _topic_purge_slugs AS s ON s.slug = t.slug
        """,
    )
    counts = connection.execute(
        sa.text(
            """
            SELECT
                (SELECT count(*) FROM topicpilot.topics) AS topic_total,
                (SELECT count(*) FROM topicpilot.topics WHERE status = 'RETIRED') AS retired_total,
                (SELECT count(*) FROM topicpilot.topics WHERE status <> 'RETIRED') AS active_total,
                (SELECT count(*) FROM _topic_purge_ids) AS target_total,
                (SELECT count(*) FROM _topic_purge_ids WHERE slug IN (
                    SELECT slug FROM topicpilot.topics WHERE status = 'RETIRED'
                )) AS target_retired_total
            """
        )
    ).one()
    if (
        counts.topic_total != EXPECTED_TOPIC_TOTAL
        or counts.retired_total != EXPECTED_RETIRED_TOTAL
        or counts.active_total != EXPECTED_ACTIVE_TOTAL
        or counts.target_total != EXPECTED_RETIRED_TOTAL
        or counts.target_retired_total != EXPECTED_RETIRED_TOTAL
    ):
        raise RuntimeError(
            "0050 precondition failed: expected 140 topics, 8 retired targets, "
            f"got total={counts.topic_total}, retired={counts.retired_total}, "
            f"active={counts.active_total}, "
            f"targets={counts.target_total}, retired_targets={counts.target_retired_total}"
        )

    # Capture dependency identities before deleting any parent rows.  The
    # temporary sets make the purge explicit and keep unrelated instruments,
    # observations, and canonical market data outside the deletion boundary.
    for name, statement in {
        "_topic_purge_relation_ids": """
            CREATE TEMP TABLE _topic_purge_relation_ids ON COMMIT DROP AS
            SELECT r.id
            FROM topicpilot.instrument_topic_relations AS r
            JOIN _topic_purge_ids AS t ON t.id = r.topic_id
        """,
        "_topic_purge_snapshot_ids": """
            CREATE TEMP TABLE _topic_purge_snapshot_ids ON COMMIT DROP AS
            SELECT s.id
            FROM topicpilot.topic_snapshots AS s
            JOIN _topic_purge_ids AS t ON t.id = s.topic_id
        """,
        "_topic_purge_projection_ids": """
            CREATE TEMP TABLE _topic_purge_projection_ids ON COMMIT DROP AS
            SELECT p.id
            FROM topicpilot.topic_score_projections AS p
            JOIN _topic_purge_ids AS t ON t.id = p.topic_id
        """,
        "_topic_purge_relation_weight_ids": """
            CREATE TEMP TABLE _topic_purge_relation_weight_ids ON COMMIT DROP AS
            SELECT DISTINCT w.id
            FROM topicpilot.relation_weight_authorities AS w
            LEFT JOIN _topic_purge_ids AS t ON t.id = w.topic_id
            LEFT JOIN _topic_purge_relation_ids AS r ON r.id = w.relation_id
            WHERE t.id IS NOT NULL OR r.id IS NOT NULL
        """,
        "_topic_purge_score_formal_ids": """
            CREATE TEMP TABLE _topic_purge_score_formal_ids ON COMMIT DROP AS
            SELECT DISTINCT f.id
            FROM topicpilot.topic_score_formal_results AS f
            LEFT JOIN _topic_purge_ids AS t ON t.id = f.topic_id
            LEFT JOIN _topic_purge_snapshot_ids AS s ON s.id = f.input_snapshot_id
            WHERE t.id IS NOT NULL OR s.id IS NOT NULL
        """,
        "_topic_purge_lifecycle_formal_ids": """
            CREATE TEMP TABLE _topic_purge_lifecycle_formal_ids ON COMMIT DROP AS
            SELECT DISTINCT f.id
            FROM topicpilot.topic_lifecycle_formal_results AS f
            LEFT JOIN _topic_purge_ids AS t ON t.id = f.topic_id
            LEFT JOIN _topic_purge_snapshot_ids AS s ON s.id = f.input_snapshot_id
            WHERE t.id IS NOT NULL OR s.id IS NOT NULL
        """,
        "_topic_purge_lifecycle_ids": """
            CREATE TEMP TABLE _topic_purge_lifecycle_ids ON COMMIT DROP AS
            SELECT DISTINCT l.id
            FROM topicpilot.topic_lifecycle_results AS l
            LEFT JOIN _topic_purge_ids AS t ON t.id = l.topic_id
            LEFT JOIN _topic_purge_snapshot_ids AS s1 ON s1.id = l.snapshot_id
            LEFT JOIN _topic_purge_snapshot_ids AS s2 ON s2.id = l.supersedes_snapshot_id
            LEFT JOIN _topic_purge_snapshot_ids AS s3 ON s3.id = l.superseded_by_snapshot_id
            WHERE t.id IS NOT NULL
               OR s1.id IS NOT NULL
               OR s2.id IS NOT NULL
               OR s3.id IS NOT NULL
        """,
    }.items():
        _execute(connection, statement)

    # Remove descendants of the captured identities first.  Self-referential
    # lineage is detached only where it points at a row being purged; no
    # unrelated stock, instrument, or observation row is deleted.
    _execute(
        connection,
        """
        DELETE FROM topicpilot.topic_score_projection_members
        WHERE projection_id IN (SELECT id FROM _topic_purge_projection_ids)
           OR structural_role_authority_id IN (SELECT id FROM _topic_purge_relation_ids)
        """,
    )
    _execute(
        connection,
        """
        UPDATE topicpilot.relation_weight_authorities
        SET supersedes_id = NULL
        WHERE supersedes_id IN (SELECT id FROM _topic_purge_relation_weight_ids)
        """,
    )
    _execute(
        connection,
        """
        DELETE FROM topicpilot.relation_weight_authorities
        WHERE id IN (SELECT id FROM _topic_purge_relation_weight_ids)
        """,
    )
    _execute(
        connection,
        """
        UPDATE topicpilot.topic_score_formal_results
        SET supersedes_decision_id = NULL
        WHERE supersedes_decision_id IN (SELECT id FROM _topic_purge_score_formal_ids)
        """,
    )
    _execute(
        connection,
        """
        DELETE FROM topicpilot.topic_score_formal_results
        WHERE id IN (SELECT id FROM _topic_purge_score_formal_ids)
        """,
    )
    _execute(
        connection,
        """
        UPDATE topicpilot.topic_lifecycle_formal_results
        SET supersedes_decision_id = NULL
        WHERE supersedes_decision_id IN (SELECT id FROM _topic_purge_lifecycle_formal_ids)
        """,
    )
    _execute(
        connection,
        """
        DELETE FROM topicpilot.topic_lifecycle_formal_results
        WHERE id IN (SELECT id FROM _topic_purge_lifecycle_formal_ids)
        """,
    )
    _execute(
        connection,
        """
        DELETE FROM topicpilot.topic_lifecycle_results
        WHERE id IN (SELECT id FROM _topic_purge_lifecycle_ids)
        """,
    )
    _execute(
        connection,
        """
        DELETE FROM topicpilot.topic_snapshot_member_facts
        WHERE snapshot_id IN (SELECT id FROM _topic_purge_snapshot_ids)
        """,
    )
    _execute(
        connection,
        """
        UPDATE topicpilot.topic_snapshots
        SET supersedes_snapshot_id = NULL
        WHERE supersedes_snapshot_id IN (SELECT id FROM _topic_purge_snapshot_ids)
        """,
    )
    _execute(
        connection,
        """
        UPDATE topicpilot.topic_snapshots
        SET superseded_by_snapshot_id = NULL
        WHERE superseded_by_snapshot_id IN (SELECT id FROM _topic_purge_snapshot_ids)
        """,
    )
    _execute(
        connection,
        """
        DELETE FROM topicpilot.topic_snapshots
        WHERE id IN (SELECT id FROM _topic_purge_snapshot_ids)
        """,
    )
    _execute(
        connection,
        """
        UPDATE topicpilot.topic_score_projections
        SET supersedes_projection_id = NULL
        WHERE supersedes_projection_id IN (SELECT id FROM _topic_purge_projection_ids)
        """,
    )
    _execute(
        connection,
        """
        UPDATE topicpilot.topic_score_projections
        SET superseded_by_projection_id = NULL
        WHERE superseded_by_projection_id IN (SELECT id FROM _topic_purge_projection_ids)
        """,
    )
    _execute(
        connection,
        """
        DELETE FROM topicpilot.topic_score_projections
        WHERE id IN (SELECT id FROM _topic_purge_projection_ids)
        """,
    )
    _execute(
        connection,
        """
        UPDATE topicpilot.instrument_topic_relations
        SET supersedes_authority_id = NULL
        WHERE supersedes_authority_id IN (SELECT id FROM _topic_purge_relation_ids)
        """,
    )
    _execute(
        connection,
        """
        UPDATE topicpilot.instrument_topic_relations
        SET superseded_by_authority_id = NULL
        WHERE superseded_by_authority_id IN (SELECT id FROM _topic_purge_relation_ids)
        """,
    )
    _execute(
        connection,
        """
        DELETE FROM topicpilot.instrument_topic_relations
        WHERE id IN (SELECT id FROM _topic_purge_relation_ids)
        """,
    )
    _execute(
        connection,
        """
        DELETE FROM topicpilot.topic_hierarchy
        WHERE parent_topic_id IN (SELECT id FROM _topic_purge_ids)
           OR child_topic_id IN (SELECT id FROM _topic_purge_ids)
        """,
    )
    _execute(
        connection,
        """
        DELETE FROM topicpilot.topics
        WHERE id IN (SELECT id FROM _topic_purge_ids)
        """,
    )


def downgrade() -> None:
    raise RuntimeError("0050 is a destructive data cleanup and cannot be downgraded")
