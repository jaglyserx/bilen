import math

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import distinct, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models import Manufacturer, Product, ProductFitment, Vehicle
from app.schemas import FilterOptions, Page, ProductDetail

router = APIRouter(prefix="/api/v1")


def product_options():
    return (
        selectinload(Product.manufacturer),
        selectinload(Product.prices),
        selectinload(Product.fitments).selectinload(ProductFitment.vehicle),
        selectinload(Product.inventory),
        selectinload(Product.links),
        selectinload(Product.categories),
    )


@router.get("/health")
def health(db: Session = Depends(get_db)) -> dict[str, str]:
    db.execute(select(1))
    return {"status": "ok"}


@router.get("/products", response_model=Page)
def list_products(
    q: str | None = None,
    manufacturer: str | None = None,
    towbar_type: str | None = None,
    vehicle_make: str | None = None,
    status: str | None = "active",
    page: int = Query(1, ge=1),
    page_size: int = Query(24, ge=1, le=100),
    sort: str = Query("name", pattern="^(name|manufacturer|article_number)$"),
    db: Session = Depends(get_db),
) -> Page:
    stmt = select(Product).join(Product.manufacturer)
    if q or vehicle_make:
        stmt = stmt.outerjoin(Product.fitments).outerjoin(ProductFitment.vehicle)
    if q:
        pattern = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                Product.article_number.ilike(pattern),
                Product.ean.ilike(pattern),
                Product.name.ilike(pattern),
                Product.towbar_type.ilike(pattern),
                Product.description.ilike(pattern),
                Manufacturer.name.ilike(pattern),
                Vehicle.source_label.ilike(pattern),
                Vehicle.make.ilike(pattern),
                Vehicle.model.ilike(pattern),
            )
        )
    if manufacturer:
        stmt = stmt.where(func.lower(Manufacturer.name) == manufacturer.casefold().strip())
    if towbar_type:
        stmt = stmt.where(Product.towbar_type == towbar_type)
    if vehicle_make:
        stmt = stmt.where(func.lower(Vehicle.make) == vehicle_make.casefold())
    if status:
        stmt = stmt.where(Product.status == status)
    count_stmt = select(func.count()).select_from(stmt.distinct().subquery())
    total = db.scalar(count_stmt) or 0
    order = {
        "name": Product.name,
        "manufacturer": Manufacturer.name,
        "article_number": Product.article_number,
    }[sort]
    stmt = (
        stmt.distinct()
        .order_by(order.asc().nullslast(), Product.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = db.scalars(stmt.options(*product_options())).unique().all()
    return Page(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        pages=math.ceil(total / page_size) if total else 0,
    )


@router.get("/products/{product_id}", response_model=ProductDetail)
def get_product(product_id: str, db: Session = Depends(get_db)) -> Product:
    product = db.scalar(select(Product).where(Product.id == product_id).options(*product_options()))
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get("/filters", response_model=FilterOptions)
def filters(db: Session = Depends(get_db)) -> FilterOptions:
    def values(column):
        return [
            value
            for value in db.scalars(
                select(distinct(column)).where(column.is_not(None)).order_by(column)
            ).all()
            if value
        ]

    return FilterOptions(
        manufacturers=values(Manufacturer.name),
        towbar_types=values(Product.towbar_type),
        vehicle_makes=values(Vehicle.make),
        statuses=values(Product.status),
    )
