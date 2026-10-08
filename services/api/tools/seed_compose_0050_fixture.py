"""Prepare the disposable Compose database for the guarded 0050 smoke path."""

from __future__ import annotations

import os
import uuid

from sqlalchemy import create_engine, text

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


def main() -> None:
    engine = create_engine(os.environ["DATABASE_URL"])
    with engine.begin() as connection:
        unexpected_retired = connection.execute(
            text(
                """
                SELECT slug
                FROM topicpilot.topics
                WHERE status = 'RETIRED' AND slug <> ALL(:target_slugs)
                """
            ),
            {"target_slugs": list(TARGET_SLUGS)},
        ).scalars().all()
        if unexpected_retired:
            raise RuntimeError(f"unexpected retired Compose fixture topics: {unexpected_retired}")

        for slug in TARGET_SLUGS:
            connection.execute(
                text(
                    """
                    INSERT INTO topicpilot.topics
                        (id, slug, name, status, dictionary_version, valid_from)
                    VALUES
                        (:id, :slug, :name, 'RETIRED', 'compose-0050-fixture.v1', DATE '2026-01-01')
                    ON CONFLICT (slug) DO UPDATE
                    SET status = 'RETIRED'
                    """
                ),
                {
                    "id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"compose-0050-fixture:{slug}")),
                    "slug": slug,
                    "name": slug,
                },
            )

        current_total = connection.execute(
            text("SELECT count(*) FROM topicpilot.topics")
        ).scalar_one()
        for index in range(EXPECTED_TOPIC_TOTAL):
            if current_total >= EXPECTED_TOPIC_TOTAL:
                break
            connection.execute(
                text(
                    """
                    INSERT INTO topicpilot.topics
                        (id, slug, name, status, dictionary_version, valid_from)
                    VALUES
                        (:id, :slug, :name, 'ENABLED', 'compose-0050-fixture.v1', DATE '2026-01-01')
                    ON CONFLICT (slug) DO NOTHING
                    """
                ),
                {
                    "id": str(
                        uuid.uuid5(uuid.NAMESPACE_URL, f"compose-0050-fixture:enabled:{index}")
                    ),
                    "slug": f"compose-0050-enabled-{index:03d}",
                    "name": f"Compose 0050 Enabled {index:03d}",
                },
            )
            current_total = connection.execute(
                text("SELECT count(*) FROM topicpilot.topics")
            ).scalar_one()

        counts = connection.execute(
            text(
                """
                SELECT count(*) AS total,
                       count(*) FILTER (WHERE status = 'RETIRED') AS retired,
                       count(*) FILTER (WHERE status <> 'RETIRED') AS active
                FROM topicpilot.topics
                """
            )
        ).one()
    engine.dispose()

    assert (counts.total, counts.retired, counts.active) == (140, 8, 132), counts


if __name__ == "__main__":
    main()
