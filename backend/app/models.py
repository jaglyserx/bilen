import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.database import Base


def uuid_string() -> str:
    return str(uuid.uuid4())


json_type = JSON().with_variant(JSONB, "postgresql")

product_categories = Table(
    "product_categories",
    Base.metadata,
    Column("product_id", ForeignKey("products.id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True),
)


class Manufacturer(Base):
    __tablename__ = "manufacturers"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    name: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    normalized_name: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    products: Mapped[list["Product"]] = relationship(back_populates="manufacturer")


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (UniqueConstraint("manufacturer_id", "normalized_article_number"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    manufacturer_id: Mapped[str] = mapped_column(ForeignKey("manufacturers.id"), index=True)
    article_number: Mapped[str] = mapped_column(String(200), index=True)
    normalized_article_number: Mapped[str] = mapped_column(String(200), index=True)
    name: Mapped[str | None] = mapped_column(String(500))
    towbar_type: Mapped[str | None] = mapped_column(String(250), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    internal_notes: Mapped[str | None] = mapped_column(Text)
    ean: Mapped[str | None] = mapped_column(String(32), index=True)
    status: Mapped[str] = mapped_column(String(30), default="active", index=True)
    webshop_visible: Mapped[bool] = mapped_column(Boolean, default=False)
    woocommerce_id: Mapped[str | None] = mapped_column(String(64), index=True)
    webshop_url: Mapped[str | None] = mapped_column(Text)
    max_towing_weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    max_ball_weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    cutout_required: Mapped[bool | None] = mapped_column(Boolean)
    lockable: Mapped[bool | None] = mapped_column(Boolean)
    size: Mapped[str | None] = mapped_column(String(100))
    installation_minutes: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
    manufacturer: Mapped[Manufacturer] = relationship(back_populates="products")
    fitments: Mapped[list["ProductFitment"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )
    prices: Mapped[list["Price"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )
    inventory: Mapped[list["Inventory"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )
    links: Mapped[list["ProductLink"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )
    categories: Mapped[list["Category"]] = relationship(
        secondary=product_categories, back_populates="products"
    )


class Vehicle(Base):
    __tablename__ = "vehicles"
    __table_args__ = (UniqueConstraint("normalized_label"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    make: Mapped[str | None] = mapped_column(String(150), index=True)
    model: Mapped[str | None] = mapped_column(String(250), index=True)
    body_style: Mapped[str | None] = mapped_column(String(150))
    year_from: Mapped[int | None] = mapped_column(Integer, index=True)
    year_to: Mapped[int | None] = mapped_column(Integer, index=True)
    source_label: Mapped[str] = mapped_column(String(500))
    normalized_label: Mapped[str] = mapped_column(String(500), index=True)
    legacy_model_id: Mapped[str | None] = mapped_column(String(64))
    fitments: Mapped[list["ProductFitment"]] = relationship(back_populates="vehicle")


class ProductFitment(Base):
    __tablename__ = "product_fitments"
    __table_args__ = (UniqueConstraint("product_id", "vehicle_id", "fitment_notes"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    product_id: Mapped[str] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    vehicle_id: Mapped[str] = mapped_column(
        ForeignKey("vehicles.id", ondelete="CASCADE"), index=True
    )
    fitment_notes: Mapped[str] = mapped_column(Text, default="")
    electrical_connection: Mapped[str | None] = mapped_column(Text)
    camper_van_notes: Mapped[str | None] = mapped_column(Text)
    product: Mapped[Product] = relationship(back_populates="fitments")
    vehicle: Mapped[Vehicle] = relationship(back_populates="fitments")


class Price(Base):
    __tablename__ = "prices"
    __table_args__ = (UniqueConstraint("product_id", "kind", "currency"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    product_id: Mapped[str] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[str] = mapped_column(String(50))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3), default="SEK")
    vat_included: Mapped[bool] = mapped_column(Boolean, default=False)
    product: Mapped[Product] = relationship(back_populates="prices")


class Inventory(Base):
    __tablename__ = "inventory"
    __table_args__ = (UniqueConstraint("product_id", "location"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    product_id: Mapped[str] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    location: Mapped[str] = mapped_column(String(100))
    quantity: Mapped[int | None] = mapped_column(Integer)
    availability: Mapped[str | None] = mapped_column(String(100))
    product: Mapped[Product] = relationship(back_populates="inventory")


class Category(Base):
    __tablename__ = "categories"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    name: Mapped[str] = mapped_column(String(250), unique=True)
    slug: Mapped[str] = mapped_column(String(250), unique=True, index=True)
    parent_id: Mapped[str | None] = mapped_column(ForeignKey("categories.id"))
    products: Mapped[list[Product]] = relationship(
        secondary=product_categories, back_populates="categories"
    )


class ProductLink(Base):
    __tablename__ = "product_links"
    __table_args__ = (UniqueConstraint("product_id", "kind", "url"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    product_id: Mapped[str] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[str] = mapped_column(String(50))
    url: Mapped[str] = mapped_column(Text)
    product: Mapped[Product] = relationship(back_populates="links")


class ImportRun(Base):
    __tablename__ = "import_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    source: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="running")
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    inserted: Mapped[int] = mapped_column(Integer, default=0)
    updated: Mapped[int] = mapped_column(Integer, default=0)
    skipped: Mapped[int] = mapped_column(Integer, default=0)
    warnings: Mapped[int] = mapped_column(Integer, default=0)
    rows: Mapped[list["ImportRow"]] = relationship(cascade="all, delete-orphan")


class ImportRow(Base):
    __tablename__ = "import_rows"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    import_run_id: Mapped[str] = mapped_column(
        ForeignKey("import_runs.id", ondelete="CASCADE"), index=True
    )
    row_number: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(30))
    message: Mapped[str | None] = mapped_column(Text)
    raw_data: Mapped[dict] = mapped_column(json_type)
