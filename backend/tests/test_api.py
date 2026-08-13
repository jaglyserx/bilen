from datetime import UTC, datetime

from app.models import Customer, Manufacturer, Order, Product


def test_health(client):
    assert client.get("/api/v1/health").json() == {"status": "ok"}


def test_search_product(client, session):
    manufacturer = Manufacturer(name="Steinhof", normalized_name="steinhof")
    session.add(manufacturer)
    session.flush()
    session.add(
        Product(
            manufacturer_id=manufacturer.id,
            article_number="A-035",
            normalized_article_number="a035",
            name="Fast dragkrok",
        )
    )
    session.commit()
    response = client.get("/api/v1/products", params={"q": "A-035"})
    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_orders_sort_open_statuses_before_done_then_by_newest(client, session):
    customer = Customer(name="Testkund")
    session.add(customer)
    session.flush()
    for external_id, status, day in (
        ("completed-newest", "completed", 4),
        ("open-older", "in_progress", 2),
        ("open-newer", "in_progress", 3),
        ("attention", "attention", 1),
        ("cancelled", "cancelled", 5),
    ):
        session.add(
            Order(
                source="test",
                external_id=external_id,
                customer_id=customer.id,
                ordered_at=datetime(2024, 1, day, tzinfo=UTC),
                status=status,
                source_sheet="test",
                source_row=day,
            )
        )
    session.commit()

    response = client.get("/api/v1/orders")

    assert response.status_code == 200
    assert [order["external_id"] for order in response.json()["items"]] == [
        "attention",
        "open-newer",
        "open-older",
        "completed-newest",
        "cancelled",
    ]
