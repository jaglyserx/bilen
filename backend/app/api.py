import math
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import case, distinct, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.importers.catalogue import normalize
from app.models import (
    Customer,
    Manufacturer,
    Order,
    OrderEvent,
    OrderItem,
    Product,
    ProductFitment,
    Vehicle,
    Workshop,
)
from app.schemas import (
    FilterOptions,
    OrderCreate,
    OrderOut,
    OrderPage,
    OrderSummary,
    Page,
    ProductDetail,
    WorkshopOut,
    WorkshopPage,
)

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
    vehicle: str | None = None,
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
    if q or vehicle or vehicle_make:
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
    if vehicle:
        vehicle_pattern = f"%{vehicle.strip()}%"
        normalized_vehicle_pattern = f"%{normalize(vehicle)}%"
        stmt = stmt.where(
            or_(
                Vehicle.source_label.ilike(vehicle_pattern),
                Vehicle.model.ilike(vehicle_pattern),
                Vehicle.normalized_label.ilike(normalized_vehicle_pattern),
            )
        )
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


def order_options():
    return (
        selectinload(Order.customer),
        selectinload(Order.workshop),
        selectinload(Order.items).selectinload(OrderItem.product),
    )


@router.get("/orders", response_model=OrderPage)
def list_orders(
    q: str | None = None,
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> OrderPage:
    stmt = select(Order).join(Order.customer)
    if q:
        pattern = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                Order.external_id.ilike(pattern),
                Order.registration_number.ilike(pattern),
                Customer.name.ilike(pattern),
                Customer.email.ilike(pattern),
            )
        )
    if status:
        stmt = stmt.where(Order.status == status)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    status_priority = case(
        (Order.status == "attention", 0),
        (Order.status == "backorder", 1),
        (Order.status == "in_progress", 2),
        (Order.status == "completed", 3),
        (Order.status == "cancelled", 4),
        else_=2,
    )
    items = (
        db.scalars(
            stmt.order_by(
                status_priority,
                Order.ordered_at.desc().nullslast(),
                Order.external_id.desc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
            .options(*order_options())
        )
        .unique()
        .all()
    )
    return OrderPage(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        pages=math.ceil(total / page_size) if total else 0,
    )


@router.get("/orders/summary", response_model=OrderSummary)
def order_summary(db: Session = Depends(get_db)) -> OrderSummary:
    statuses = {
        status: count
        for status, count in db.execute(
            select(Order.status, func.count()).group_by(Order.status)
        ).tuples()
    }
    return OrderSummary(
        total=sum(statuses.values()),
        by_status=statuses,
        unmatched_items=db.scalar(
            select(func.count()).select_from(OrderItem).where(OrderItem.product_id.is_(None))
        )
        or 0,
    )


@router.post("/orders", response_model=OrderOut, status_code=201)
def create_order(data: OrderCreate, db: Session = Depends(get_db)) -> Order:
    workshop = db.get(Workshop, data.workshop_id)
    if not workshop or not workshop.is_active:
        raise HTTPException(status_code=422, detail="Choose an active workshop")
    product_ids = list(dict.fromkeys(item.product_id for item in data.items))
    products = {
        product.id: product
        for product in db.scalars(select(Product).where(Product.id.in_(product_ids))).all()
    }
    missing = [product_id for product_id in product_ids if product_id not in products]
    if missing:
        raise HTTPException(status_code=422, detail={"unknown_product_ids": missing})

    now = datetime.now(UTC)
    customer = Customer(**data.customer.model_dump())
    order = Order(
        source="crm",
        external_id=f"CRM-{now:%Y%m%d}-{uuid.uuid4().hex[:8].upper()}",
        customer=customer,
        workshop=workshop,
        ordered_at=now,
        status="in_progress",
        workflow_status="Ny order",
        sales_channel="crm",
        registration_number=data.registration_number,
        vehicle_label=data.vehicle_label,
        vehicle_year=data.vehicle_year,
        notes=data.notes,
        sales_person=data.sales_person,
        source_sheet="crm",
        source_row=0,
    )
    for position, item in enumerate(data.items, start=1):
        product = products[item.product_id]
        order.items.append(
            OrderItem(
                position=position,
                kind="product",
                product=product,
                source_sku=product.article_number,
                description=product.name or product.article_number,
                quantity=item.quantity,
                link_status="linked",
            )
        )
    order.events.append(
        OrderEvent(
            event_type="order.created",
            payload={
                "schema_version": 1,
                "workshop_id": workshop.id,
                "product_ids": [item.product_id for item in data.items],
            },
        )
    )
    db.add(order)
    db.commit()
    created = db.scalar(select(Order).where(Order.id == order.id).options(*order_options()))
    if created is None:  # pragma: no cover - guarded by the successful transaction above
        raise HTTPException(status_code=500, detail="Created order could not be loaded")
    return created


@router.get("/orders/{order_id}", response_model=OrderOut)
def get_order(order_id: str, db: Session = Depends(get_db)) -> Order:
    order = db.scalar(select(Order).where(Order.id == order_id).options(*order_options()))
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.get("/workshops", response_model=WorkshopPage)
def list_workshops(
    q: str | None = None,
    city: str | None = None,
    postal_prefix: str | None = Query(default=None, min_length=2, max_length=3),
    active: bool | None = True,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> WorkshopPage:
    stmt = select(Workshop)
    if q:
        pattern = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                Workshop.name.ilike(pattern),
                Workshop.city.ilike(pattern),
                Workshop.postal_code.ilike(pattern),
                Workshop.contact_person.ilike(pattern),
            )
        )
    if city:
        stmt = stmt.where(func.lower(Workshop.city) == city.casefold().strip())
    if postal_prefix:
        normalized_prefix = "".join(character for character in postal_prefix if character.isdigit())
        if len(normalized_prefix) < 2:
            raise HTTPException(status_code=422, detail="Postal prefix must contain two digits")
        stmt = stmt.where(func.replace(Workshop.postal_code, " ", "").like(f"{normalized_prefix}%"))
    if active is not None:
        stmt = stmt.where(Workshop.is_active == active)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = db.scalars(
        stmt.order_by(Workshop.city.asc().nullslast(), Workshop.name.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return WorkshopPage(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        pages=math.ceil(total / page_size) if total else 0,
    )


@router.get("/workshops/{workshop_id}", response_model=WorkshopOut)
def get_workshop(workshop_id: str, db: Session = Depends(get_db)) -> Workshop:
    workshop = db.get(Workshop, workshop_id)
    if not workshop:
        raise HTTPException(status_code=404, detail="Workshop not found")
    return workshop
