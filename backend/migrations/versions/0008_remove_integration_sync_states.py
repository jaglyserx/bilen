"""Remove the cursor table after switching to a fixed rolling lookback."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008_remove_integration_sync_states"
down_revision: str | None = "0007_integration_sync_states"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_table("integration_sync_states")


def downgrade() -> None:
    op.create_table(
        "integration_sync_states",
        sa.Column("name", sa.String(length=100), primary_key=True),
        sa.Column("cursor_at", sa.DateTime(timezone=True)),
        sa.Column("last_started_at", sa.DateTime(timezone=True)),
        sa.Column("last_completed_at", sa.DateTime(timezone=True)),
        sa.Column("last_imported", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_unmatched", sa.Integer(), nullable=False, server_default="0"),
    )
