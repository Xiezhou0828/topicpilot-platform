"""Reconcile the remote reference-transition branch with the WS1 release head.

The remote ``0030_task_data_ref_006g_registry_transition`` migration is
preserved as a real branch.  The local canonical lineage owns a different
0030 revision and continues through 0032.  This standard Alembic merge
revision creates one intentional release head without rewriting either
revision ID or skipping the remote table semantics.
"""

revision = "0033_task_ws4_reference_registry_transition_merge"
down_revision = (
    "0032_task_ws1_topic_lifecycle_contract_gap_closure",
    "0030_task_data_ref_006g_registry_transition",
)
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Both parent branches have already applied their schema changes."""


def downgrade() -> None:
    """Downgrade is represented by Alembic traversing both parent branches."""
