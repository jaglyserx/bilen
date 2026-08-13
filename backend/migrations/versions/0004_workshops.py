"""Add collaborating workshops."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_workshops"
down_revision: str | None = "0003_order_vehicle_fields"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "workshops",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("normalized_name", sa.String(500), nullable=False),
        sa.Column("contact_person", sa.String(500)),
        sa.Column("address", sa.Text()),
        sa.Column("postal_code", sa.String(30)),
        sa.Column("city", sa.String(200)),
        sa.Column("phone", sa.Text()),
        sa.Column("email", sa.Text()),
        sa.Column("organization_number", sa.String(100)),
        sa.Column("booking_instructions", sa.Text()),
        sa.Column("agreement_terms", sa.Text()),
        sa.Column("workshop_info", sa.Text()),
        sa.Column("discount_terms", sa.Text()),
        sa.Column("internal_owner", sa.String(200)),
        sa.Column("written_agreement", sa.Boolean()),
        sa.Column("terms_updated_at", sa.DateTime(timezone=True)),
        sa.Column("current_info", sa.Text()),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("restrictions", sa.Text()),
        sa.Column("supports_motorhomes", sa.Boolean()),
        sa.Column("loan_car_available", sa.Boolean()),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("source_sheet", sa.String(100), nullable=False),
        sa.Column("source_row", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("source", "source_sheet", "source_row"),
    )
    for column in (
        "name",
        "normalized_name",
        "postal_code",
        "city",
        "internal_owner",
        "is_active",
        "supports_motorhomes",
        "loan_car_available",
    ):
        op.create_index(f"ix_workshops_{column}", "workshops", [column])


def downgrade() -> None:
    op.drop_table("workshops")
