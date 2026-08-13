from openpyxl import Workbook
from sqlalchemy import select

from app.importers.workshops import import_workshops
from app.models import Workshop


def create_workbook(path):
    book = Workbook()
    sheet = book.active
    sheet.title = "Våra Verkstäder"
    sheet.append(["Hur boka?", "Namn", "Lånebil"])
    row = [None] * 21
    row[0:3] = ["Ring innan", "Testverkstaden", "Ja"]
    row[5:11] = ["Ada", "Testgatan 1", "123 45", "Borås", "070-123", "test@example.se"]
    row[18] = "Ja"
    row[20] = True
    sheet.append(row)
    book.save(path)


def test_workshop_import_is_idempotent(session, tmp_path):
    path = tmp_path / "lager.xlsx"
    create_workbook(path)
    assert import_workshops(path, session) == 1
    assert import_workshops(path, session) == 1
    workshops = session.scalars(select(Workshop)).all()
    assert len(workshops) == 1
    assert workshops[0].city == "Borås"
    assert workshops[0].is_active is True
    assert workshops[0].loan_car_available is True
    assert workshops[0].supports_motorhomes is True
