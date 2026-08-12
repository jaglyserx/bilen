"""Initial catalogue schema."""

from alembic import op

from app import models  # noqa: F401
from app.database import Base

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    Base.metadata.create_all(bind=bind)
    if bind.dialect.name == "postgresql":
        op.execute("CREATE INDEX ix_products_name_trgm ON products USING gin (name gin_trgm_ops)")
        op.execute(
            "CREATE INDEX ix_vehicles_source_label_trgm ON vehicles USING gin (source_label gin_trgm_ops)"
        )


def downgrade():
    Base.metadata.drop_all(bind=op.get_bind())
