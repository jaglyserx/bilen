import base64
import json
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select

from app.clients.woocommerce import WooCommerceClient, WooOrder
from app.importers.woocommerce_orders import import_orders
from app.models import Manufacturer, Order, Product


def woo_order(**overrides) -> WooOrder:
    payload = {
        "id": 812,
        "number": "812",
        "status": "processing",
        "currency": "sek",
        "total": "3490.00",
        "date_created_gmt": "2026-08-20T10:15:00",
        "date_paid_gmt": "2026-08-20T10:16:00",
        "payment_method_title": "Klarna",
        "customer_note": "Ring före leverans",
        "billing": {
            "first_name": "Ada",
            "last_name": "Andersson",
            "address_1": "Fakturagatan 1",
            "city": "Borås",
            "postcode": "50100",
            "email": "ada@example.se",
            "phone": "0701234567",
        },
        "shipping": {
            "first_name": "Ada",
            "last_name": "Andersson",
            "address_1": "Leveransgatan 2",
            "address_2": "c/o Test",
            "city": "Göteborg",
            "postcode": "41101",
        },
        "meta_data": [
            {"key": "registreringsnummer", "value": "ABC123"},
            {"key": "bilmodell", "value": "Volvo V70"},
        ],
        "line_items": [
            {
                "id": 1,
                "name": "Fast dragkrok",
                "product_id": 456,
                "quantity": 2,
                "sku": "SKU-1",
            }
        ],
    }
    payload.update(overrides)
    return WooOrder.model_validate(payload)


class FakeClient:
    def __init__(self, orders):
        self.orders = orders

    def iter_orders(self):
        yield from self.orders


def test_client_uses_basic_auth_and_parses_orders(monkeypatch):
    captured = {}

    class Response:
        headers = {"X-WP-TotalPages": "3"}

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def read(self):
            return json.dumps([woo_order().model_dump(mode="json")]).encode()

    def fake_urlopen(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setattr("app.clients.woocommerce.urlopen", fake_urlopen)
    client = WooCommerceClient("https://shop.example", "ck_test", "cs_test", timeout=12)

    orders, pages = client.get_orders(page=2)

    assert pages == 3
    assert orders[0].id == 812
    assert captured["timeout"] == 12
    assert "page=2" in captured["request"].full_url
    expected = base64.b64encode(b"ck_test:cs_test").decode()
    assert captured["request"].get_header("Authorization") == f"Basic {expected}"
    assert "ck_test" not in captured["request"].full_url


def test_import_maps_to_existing_order_and_is_idempotent(session):
    product = Product(
        manufacturer=Manufacturer(name="Test", normalized_name="test"),
        article_number="SKU-1",
        normalized_article_number="sku1",
        name="Fast dragkrok",
        woocommerce_id="456",
    )
    session.add(product)
    session.commit()
    client = FakeClient([woo_order()])

    assert import_orders(client, session) == (1, 0)
    assert import_orders(client, session) == (1, 0)

    orders = session.scalars(select(Order)).all()
    assert len(orders) == 1
    order = orders[0]
    assert order.source == "woocommerce"
    assert order.external_id == "812"
    assert order.status == "in_progress"
    assert order.workflow_status == "processing"
    assert order.ordered_at == datetime(2026, 8, 20, 10, 15, tzinfo=UTC)
    assert order.confirmed_at == datetime(2026, 8, 20, 10, 16, tzinfo=UTC)
    assert order.total_amount == Decimal("3490.00")
    assert order.currency == "SEK"
    assert order.registration_number == "ABC123"
    assert order.vehicle_label == "Volvo V70"
    assert order.customer.name == "Ada Andersson"
    assert order.customer.delivery_address == "Leveransgatan 2 c/o Test"
    assert order.customer.city == "Göteborg"
    assert len(order.items) == 1
    assert order.items[0].quantity == 2
    assert order.items[0].product_id == product.id
    assert order.items[0].link_status == "linked"


def test_import_leaves_unknown_product_visible(session):
    source = woo_order(
        line_items=[
            {
                "id": 2,
                "name": "Okänd produkt",
                "product_id": 999,
                "quantity": 1,
                "sku": "UNKNOWN",
            }
        ]
    )
    imported, unmatched = import_orders(FakeClient([source]), session)

    assert (imported, unmatched) == (1, 1)
    item = session.scalars(select(Order)).one().items[0]
    assert item.product is None
    assert item.link_status == "unmatched"
