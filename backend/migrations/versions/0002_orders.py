"""Add customers, orders, order items, and stable product identifiers."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_orders"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    existing = set(sa.inspect(op.get_bind()).get_table_names())
    if "product_identifiers" not in existing:
        op.create_table(
            "product_identifiers",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column(
                "product_id",
                sa.String(36),
                sa.ForeignKey("products.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("kind", sa.String(30), nullable=False),
            sa.Column("value", sa.String(200), nullable=False),
            sa.Column("normalized_value", sa.String(200), nullable=False),
            sa.UniqueConstraint("kind", "normalized_value"),
        )
        op.create_index("ix_product_identifiers_product_id", "product_identifiers", ["product_id"])
        op.create_index(
            "ix_product_identifiers_normalized_value",
            "product_identifiers",
            ["normalized_value"],
        )
    # Only globally unique article numbers are safe identifiers. Duplicate values are
    # intentionally left out and therefore cannot silently link an order incorrectly.
    op.execute("""
        INSERT INTO product_identifiers (id, product_id, kind, value, normalized_value)
        SELECT md5(random()::text || clock_timestamp()::text), p.id,
               'article_number', p.article_number, p.normalized_article_number
        FROM products p
        JOIN (
            SELECT normalized_article_number
            FROM products GROUP BY normalized_article_number HAVING count(*) = 1
        ) unique_numbers USING (normalized_article_number)
        WHERE NOT EXISTS (
            SELECT 1 FROM product_identifiers pi
            WHERE pi.kind = 'article_number'
              AND pi.normalized_value = p.normalized_article_number
        )
    """)
    if "customers" not in existing:
        op.create_table(
            "customers",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("name", sa.String(500), nullable=False),
            sa.Column("email", sa.String(320)),
            sa.Column("phone", sa.String(100)),
            sa.Column("delivery_address", sa.Text()),
            sa.Column("postal_code", sa.String(30)),
            sa.Column("city", sa.String(200)),
        )
        op.create_index("ix_customers_name", "customers", ["name"])
        op.create_index("ix_customers_email", "customers", ["email"])
    if "orders" not in existing:
        op.create_table(
            "orders",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("source", sa.String(50), nullable=False),
            sa.Column("external_id", sa.String(100), nullable=False),
            sa.Column("customer_id", sa.String(36), sa.ForeignKey("customers.id"), nullable=False),
            sa.Column("ordered_at", sa.DateTime(timezone=True)),
            sa.Column("status", sa.String(30), nullable=False),
            sa.Column("workflow_status", sa.String(500)),
            sa.Column("sales_person", sa.String(100)),
            sa.Column("sales_channel", sa.String(100)),
            sa.Column("total_amount", sa.Numeric(12, 2)),
            sa.Column("currency", sa.String(3), nullable=False),
            sa.Column("payment_method", sa.String(200)),
            sa.Column("vehicle_label", sa.Text()),
            sa.Column("vehicle_year", sa.String(30)),
            sa.Column("registration_number", sa.String(30)),
            sa.Column("shipping_date", sa.DateTime(timezone=True)),
            sa.Column("tracking_number", sa.Text()),
            sa.Column("notes", sa.Text()),
            sa.Column("source_sheet", sa.String(100), nullable=False),
            sa.Column("source_row", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("source", "external_id"),
        )
        for column in (
            "external_id",
            "customer_id",
            "ordered_at",
            "status",
            "sales_person",
            "sales_channel",
            "registration_number",
        ):
            op.create_index(f"ix_orders_{column}", "orders", [column])
    if "order_items" not in existing:
        op.create_table(
            "order_items",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column(
                "order_id",
                sa.String(36),
                sa.ForeignKey("orders.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "product_id", sa.String(36), sa.ForeignKey("products.id", ondelete="SET NULL")
            ),
            sa.Column("position", sa.Integer(), nullable=False),
            sa.Column("kind", sa.String(30), nullable=False),
            sa.Column("source_sku", sa.String(500)),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("quantity", sa.Integer(), nullable=False),
            sa.Column("link_status", sa.String(30), nullable=False),
            sa.UniqueConstraint("order_id", "position"),
        )
        for column in ("order_id", "product_id", "source_sku", "link_status"):
            op.create_index(f"ix_order_items_{column}", "order_items", [column])


def downgrade() -> None:
    op.drop_table("order_items")
    op.drop_table("orders")
    op.drop_table("customers")
    op.drop_table("product_identifiers")
