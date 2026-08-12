from app.models import Manufacturer, Product


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
