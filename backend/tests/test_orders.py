from datetime import datetime
from decimal import Decimal
from pathlib import Path

from openpyxl import Workbook
from sqlalchemy import select

from app.importers.orders import amount, import_workbook
from app.models import Manufacturer, Order, Product, ProductIdentifier


def workbook(path: Path) -> None:
    book = Workbook()
    sheet = book.active
    sheet.title = "2024"
    sheet.append([None] * 50)
    sheet.append([None] * 50)
    row = [None] * 50
    row[1:10] = [
        "TC",
        datetime(2024, 1, 2),
        371641,
        "Ada Andersson",
        "Gatan 1",
        12345,
        "Borås",
        "070",
        "ada@example.se",
    ]
    row[12:16] = ["Fast dragkrok", "7-polig elsats", "ABC-123", None]
    row[18:22] = ["Volvo V70", 2018, "ABC123", 2990]
    row[23] = "Lager Borås KLAR"
    sheet.append(row)
    book.save(path)


def test_import_links_only_exact_identifier(session, tmp_path):
    maker = Manufacturer(name="Test", normalized_name="test")
    product = Product(
        manufacturer=maker, article_number="ABC-123", normalized_article_number="abc123"
    )
    product.identifiers.append(
        ProductIdentifier(kind="article_number", value="ABC-123", normalized_value="abc123")
    )
    session.add(product)
    session.commit()
    path = tmp_path / "orders.xlsx"
    workbook(path)

    imported, unmatched = import_workbook(path, session)
    assert (imported, unmatched) == (1, 1)
    response_items = session.query(Product).one().order_items
    assert len(response_items) == 1
    assert response_items[0].link_status == "linked"


def test_import_is_idempotent(session, tmp_path):
    path = tmp_path / "orders.xlsx"
    workbook(path)
    import_workbook(path, session)
    import_workbook(path, session)
    assert len(session.scalars(select(Order)).all()) == 1


def test_amount_rejects_phone_numbers_and_parses_swedish_prices():
    assert amount("1 595 kr + frakt") == 1595
    assert amount("1.595,50 kr") == Decimal("1595.50")
    assert amount("6401 504 9770") is None
