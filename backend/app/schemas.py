from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ManufacturerOut(BaseModel):
    id: str
    name: str
    model_config = ConfigDict(from_attributes=True)


class VehicleOut(BaseModel):
    id: str
    make: str | None
    model: str | None
    body_style: str | None
    year_from: int | None
    year_to: int | None
    source_label: str
    model_config = ConfigDict(from_attributes=True)


class FitmentOut(BaseModel):
    id: str
    fitment_notes: str
    electrical_connection: str | None
    camper_van_notes: str | None
    vehicle: VehicleOut
    model_config = ConfigDict(from_attributes=True)


class PriceOut(BaseModel):
    kind: str
    amount: Decimal
    currency: str
    vat_included: bool
    model_config = ConfigDict(from_attributes=True)


class InventoryOut(BaseModel):
    location: str
    quantity: int | None
    availability: str | None
    model_config = ConfigDict(from_attributes=True)


class LinkOut(BaseModel):
    kind: str
    url: str
    model_config = ConfigDict(from_attributes=True)


class CategoryOut(BaseModel):
    id: str
    name: str
    slug: str
    model_config = ConfigDict(from_attributes=True)


class ProductSummary(BaseModel):
    id: str
    article_number: str
    name: str | None
    towbar_type: str | None
    status: str
    ean: str | None
    webshop_url: str | None
    manufacturer: ManufacturerOut
    prices: list[PriceOut]
    fitments: list[FitmentOut]
    model_config = ConfigDict(from_attributes=True)


class ProductDetail(ProductSummary):
    description: str | None
    max_towing_weight_kg: Decimal | None
    max_ball_weight_kg: Decimal | None
    weight_kg: Decimal | None
    cutout_required: bool | None
    lockable: bool | None
    size: str | None
    installation_minutes: int | None
    inventory: list[InventoryOut]
    links: list[LinkOut]
    categories: list[CategoryOut]


class Page(BaseModel):
    items: list[ProductSummary]
    page: int
    page_size: int
    total: int
    pages: int


class FilterOptions(BaseModel):
    manufacturers: list[str]
    towbar_types: list[str]
    vehicle_makes: list[str]
    statuses: list[str]


class CustomerOut(BaseModel):
    id: str
    name: str
    email: str | None
    phone: str | None
    city: str | None
    model_config = ConfigDict(from_attributes=True)


class OrderProductOut(BaseModel):
    id: str
    article_number: str
    name: str | None
    model_config = ConfigDict(from_attributes=True)


class OrderItemOut(BaseModel):
    id: str
    kind: str
    source_sku: str | None
    description: str
    quantity: int
    link_status: str
    product: OrderProductOut | None
    model_config = ConfigDict(from_attributes=True)


class WorkshopSummaryOut(BaseModel):
    id: str
    name: str
    city: str | None
    model_config = ConfigDict(from_attributes=True)


class OrderOut(BaseModel):
    id: str
    external_id: str
    ordered_at: datetime | None
    status: str
    workflow_status: str | None
    sales_person: str | None
    sales_channel: str | None
    total_amount: Decimal | None
    currency: str
    vehicle_label: str | None
    registration_number: str | None
    customer: CustomerOut
    workshop: WorkshopSummaryOut | None
    items: list[OrderItemOut]
    model_config = ConfigDict(from_attributes=True)


class OrderPage(BaseModel):
    items: list[OrderOut]
    page: int
    page_size: int
    total: int
    pages: int


class OrderSummary(BaseModel):
    total: int
    by_status: dict[str, int]
    unmatched_items: int


class CustomerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=500)
    email: str | None = Field(default=None, max_length=320)
    phone: str | None = Field(default=None, max_length=100)
    delivery_address: str | None = None
    postal_code: str | None = Field(default=None, max_length=30)
    city: str | None = Field(default=None, max_length=200)


class OrderItemCreate(BaseModel):
    product_id: str
    quantity: int = Field(default=1, ge=1, le=100)


class OrderCreate(BaseModel):
    customer: CustomerCreate
    workshop_id: str
    items: list[OrderItemCreate] = Field(min_length=1, max_length=100)
    registration_number: str | None = None
    vehicle_label: str | None = None
    vehicle_year: str | None = None
    notes: str | None = None
    sales_person: str | None = Field(default=None, max_length=100)


class WorkshopOut(BaseModel):
    id: str
    name: str
    contact_person: str | None
    address: str | None
    postal_code: str | None
    city: str | None
    phone: str | None
    email: str | None
    booking_instructions: str | None
    agreement_terms: str | None
    workshop_info: str | None
    discount_terms: str | None
    internal_owner: str | None
    written_agreement: bool | None
    terms_updated_at: datetime | None
    current_info: str | None
    is_active: bool
    restrictions: str | None
    supports_motorhomes: bool | None
    loan_car_available: bool | None
    model_config = ConfigDict(from_attributes=True)


class WorkshopPage(BaseModel):
    items: list[WorkshopOut]
    page: int
    page_size: int
    total: int
    pages: int
