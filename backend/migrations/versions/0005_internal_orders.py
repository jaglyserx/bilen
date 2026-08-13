"""Link orders to workshops and add an integration event outbox."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_internal_orders"
down_revision: str | None = "0004_workshops"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("workshop_id", sa.String(36)))
    op.create_foreign_key(
        "fk_orders_workshop_id", "orders", "workshops", ["workshop_id"], ["id"], ondelete="SET NULL"
    )
    op.create_index("ix_orders_workshop_id", "orders", ["workshop_id"])
    op.create_table(
        "order_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "order_id",
            sa.String(36),
            sa.ForeignKey("orders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True)),
    )
    for column in ("order_id", "event_type", "occurred_at", "processed_at"):
        op.create_index(f"ix_order_events_{column}", "order_events", [column])


def downgrade() -> None:
    op.drop_table("order_events")
    op.drop_index("ix_orders_workshop_id", table_name="orders")
    op.drop_constraint("fk_orders_workshop_id", "orders", type_="foreignkey")
    op.drop_column("orders", "workshop_id")
