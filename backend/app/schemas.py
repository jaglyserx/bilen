from decimal import Decimal

from pydantic import BaseModel, ConfigDict


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
