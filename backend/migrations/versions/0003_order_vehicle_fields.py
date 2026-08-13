"""Allow orders containing multiple vehicles and registration numbers."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_order_vehicle_fields"
down_revision: str | None = "0002_orders"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column("orders", "vehicle_year", existing_type=sa.String(30), type_=sa.Text())
    op.alter_column("orders", "registration_number", existing_type=sa.String(30), type_=sa.Text())


def downgrade() -> None:
    op.alter_column("orders", "vehicle_year", existing_type=sa.Text(), type_=sa.String(30))
    op.alter_column("orders", "registration_number", existing_type=sa.Text(), type_=sa.String(30))
