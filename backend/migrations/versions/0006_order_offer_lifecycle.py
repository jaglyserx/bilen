"""Add the offer confirmation timestamp to orders."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_order_offer_lifecycle"
down_revision: str | None = "0005_internal_orders"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("confirmed_at", sa.DateTime(timezone=True)))
    op.create_index("ix_orders_confirmed_at", "orders", ["confirmed_at"])


def downgrade() -> None:
    op.drop_index("ix_orders_confirmed_at", table_name="orders")
    op.drop_column("orders", "confirmed_at")
