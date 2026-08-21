"""Idempotently import WooCommerce orders into the existing order model."""

import argparse
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clients.woocommerce import WooAddress, WooCommerceClient, WooMetaData, WooOrder
from app.config import get_settings
from app.database import SessionLocal
from app.importers.catalogue import normalize
from app.models import Customer, Order, OrderItem, Product, ProductIdentifier

STATUS_MAP = {
    "pending": "in_progress",
    "processing": "in_progress",
    "on-hold": "in_progress",
    "completed": "completed",
    "cancelled": "cancelled",
    "refunded": "cancelled",
    "failed": "cancelled",
    "trash": "cancelled",
}


class OrderSource(Protocol):
    def iter_orders(self, *, modified_after: datetime | None = None) -> Iterable[WooOrder]: ...


def _utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def _text(*values: str) -> str | None:
    result = " ".join(value.strip() for value in values if value and value.strip())
    return result or None


def _address(value: WooAddress) -> str | None:
    return _text(value.address_1, value.address_2)


def _metadata(items: list[WooMetaData], *keys: str) -> str | None:
    wanted = {key.casefold() for key in keys}
    for item in items:
        if item.key.casefold() in wanted and item.value not in (None, ""):
            return str(item.value).strip() or None
    return None


def resolve_product(
    session: Session, sku: str | None, woo_product_id: int | None
) -> Product | None:
    normalized_sku = normalize(sku)
    if normalized_sku:
        product = session.scalar(
            select(Product)
            .join(ProductIdentifier)
            .where(
                ProductIdentifier.kind == "article_number",
                ProductIdentifier.normalized_value == normalized_sku,
            )
        )
        if product:
            return product
    if woo_product_id:
        matches = session.scalars(
            select(Product).where(Product.woocommerce_id == str(woo_product_id)).limit(2)
        ).all()
        if len(matches) == 1:
            return matches[0]
    return None


def upsert_order(session: Session, source: WooOrder) -> tuple[Order, int]:
    """Translate and upsert one WooCommerce order; return it and unmatched count."""
    external_id = str(source.id)
    order = session.scalar(
        select(Order).where(Order.source == "woocommerce", Order.external_id == external_id)
    )
    if order is None:
        customer = Customer(
            name=_text(source.billing.first_name, source.billing.last_name) or "Okänd"
        )
        order = Order(
            source="woocommerce",
            external_id=external_id,
            customer=customer,
            status="in_progress",
            source_sheet="woocommerce",
            source_row=0,
        )
        session.add(order)
        session.flush()

    billing = source.billing
    shipping = source.shipping
    delivery = shipping if _address(shipping) else billing
    customer = order.customer
    customer.name = (
        _text(billing.first_name, billing.last_name)
        or _text(shipping.first_name, shipping.last_name)
        or billing.company.strip()
        or "Okänd"
    )
    customer.email = billing.email.strip() or None
    customer.phone = billing.phone.strip() or None
    customer.delivery_address = _address(delivery)
    customer.postal_code = delivery.postcode.strip() or None
    customer.city = delivery.city.strip() or None

    order.ordered_at = _utc(source.date_created_gmt or source.date_created)
    order.confirmed_at = _utc(source.date_paid_gmt)
    order.status = STATUS_MAP.get(source.status, "attention")
    order.workflow_status = source.status
    order.sales_channel = "woocommerce"
    order.total_amount = source.total
    order.currency = source.currency[:3].upper() or "SEK"
    order.payment_method = source.payment_method_title or source.payment_method or None
    order.registration_number = _metadata(
        source.meta_data,
        "registration_number",
        "_registration_number",
        "registreringsnummer",
        "regnr",
    )
    order.vehicle_label = _metadata(
        source.meta_data, "vehicle", "vehicle_label", "bilmodell", "car_model"
    )
    order.vehicle_year = _metadata(source.meta_data, "vehicle_year", "årsmodell", "year")
    order.notes = source.customer_note.strip() or None

    order.items.clear()
    session.flush()
    unmatched = 0
    for position, line in enumerate(source.line_items, start=1):
        woo_product_id = line.variation_id or line.product_id
        product = resolve_product(session, line.sku, woo_product_id)
        link_status = "linked" if product else ("missing_sku" if not line.sku else "unmatched")
        unmatched += int(product is None)
        order.items.append(
            OrderItem(
                position=position,
                kind="product",
                source_sku=line.sku.strip() or None,
                description=line.name,
                quantity=line.quantity,
                product=product,
                link_status=link_status,
            )
        )
    return order, unmatched


def import_orders(
    client: OrderSource,
    session: Session,
    *,
    modified_after: datetime | None = None,
    commit: bool = True,
) -> tuple[int, int]:
    imported = unmatched = 0
    for source in client.iter_orders(modified_after=modified_after):
        _, order_unmatched = upsert_order(session, source)
        imported += 1
        unmatched += order_unmatched
        if imported % 100 == 0:
            session.flush()
    if commit:
        session.commit()
    else:
        session.flush()
    return imported, unmatched


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    settings = get_settings()
    if not settings.woo_url or not settings.woo_key or not settings.woo_secret:
        parser.error("WOO_URL, WOO_KEY, and WOO_SECRET must be configured")
    client = WooCommerceClient(settings.woo_url, settings.woo_key, settings.woo_secret)
    with SessionLocal() as session:
        imported, unmatched = import_orders(client, session)
    print(f"WooCommerce import complete: {imported} orders, {unmatched} unmatched items")


if __name__ == "__main__":
    main()
