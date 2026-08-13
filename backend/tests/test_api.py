from datetime import UTC, datetime

from app.models import (
    Customer,
    Manufacturer,
    Order,
    OrderEvent,
    Product,
    ProductFitment,
    Vehicle,
    Workshop,
)


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


def test_create_order_links_products_workshop_and_emits_event(client, session):
    manufacturer = Manufacturer(name="Tillverkare", normalized_name="tillverkare")
    product = Product(
        manufacturer=manufacturer,
        article_number="SKU-1",
        normalized_article_number="sku1",
        name="Dragkrok",
    )
    workshop = Workshop(
        name="Aktiv verkstad",
        normalized_name="aktivverkstad",
        is_active=True,
        source="test",
        source_sheet="test",
        source_row=1,
    )
    session.add_all([product, workshop])
    session.commit()

    response = client.post(
        "/api/v1/orders",
        json={
            "customer": {"name": "Ada", "email": "ada@example.se"},
            "workshop_id": workshop.id,
            "items": [{"product_id": product.id, "quantity": 2}],
            "registration_number": "ABC123",
        },
    )

    assert response.status_code == 201
    result = response.json()
    assert result["workshop"]["id"] == workshop.id
    assert result["items"][0]["product"]["id"] == product.id
    assert result["items"][0]["quantity"] == 2
    event = session.query(OrderEvent).one()
    assert event.event_type == "order.created"
    assert event.payload["schema_version"] == 1


def test_products_can_be_filtered_by_explicit_vehicle_fitment(client, session):
    manufacturer = Manufacturer(name="Fitment", normalized_name="fitment")
    matching = Product(
        manufacturer=manufacturer,
        article_number="V70",
        normalized_article_number="v70",
        name="Passande krok",
    )
    other = Product(
        manufacturer=manufacturer,
        article_number="OTHER",
        normalized_article_number="other",
        name="Annan krok",
    )
    vehicle = Vehicle(source_label="Volvo V70 2012", normalized_label="volvov702012")
    matching.fitments.append(ProductFitment(vehicle=vehicle, fitment_notes=""))
    session.add_all([matching, other])
    session.commit()

    response = client.get("/api/v1/products", params={"vehicle": "Volvo V70"})

    assert response.status_code == 200
    assert [item["id"] for item in response.json()["items"]] == [matching.id]


def test_workshops_can_be_limited_to_postal_area(client, session):
    session.add_all(
        [
            Workshop(
                name="Nära",
                normalized_name="nara",
                postal_code="123 45",
                is_active=True,
                source="test",
                source_sheet="test",
                source_row=10,
            ),
            Workshop(
                name="Långt bort",
                normalized_name="langtbort",
                postal_code="987 65",
                is_active=True,
                source="test",
                source_sheet="test",
                source_row=11,
            ),
        ]
    )
    session.commit()

    response = client.get("/api/v1/workshops", params={"postal_prefix": "12"})

    assert response.status_code == 200
    assert [item["name"] for item in response.json()["items"]] == ["Nära"]
