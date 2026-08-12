from decimal import Decimal
from pathlib import Path

from sqlalchemy import func, select

from app.importers.catalogue import decimal_value, import_csv, normalize, parse_vehicle
from app.models import Product, ProductFitment


def test_swedish_values_are_normalized():
    assert decimal_value("1 183,20") == Decimal("1183.20")
    assert decimal_value("UTGÅTT") is None
    assert normalize("Auto-Hak A-035") == "autohaka035"


def test_vehicle_years_are_parsed():
    vehicle = parse_vehicle("ALFA ROMEO 147 Halvkombi 2001>2009", "3")
    assert vehicle["make"] == "Alfa"
    assert vehicle["year_from"] == 2001
    assert vehicle["year_to"] == 2009


def test_import_is_idempotent(tmp_path: Path, session):
    csv_file = tmp_path / "catalogue.csv"
    csv_file.write_text(
        ",,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,\n"
        ",Bilmodell ID,Tillverkare,Artikelnummer,Steinhof lager?,Borås Lager,Lager övrigt,Typ av kula,Info,Egna noteringar!,Webshop,Pris Inköp,Kundpris ex moms,Kundpris inkl moms,_regular_price,Pris webshop inkl moms,Exkl moms,Monteringsanvisning,Pris webshop exkl moms,Kopplingsschema,7-can,13-can,7-spec,13-spec,Plåtis,Pristillägg,Namn,Kategori,Max dragvikt,Max kultryck,Vikt,Utskärning,Monteringstid,Inkoppling,EAN,Låsbar,Storlek,,id-woocommerce,URL webshop\n"
        'ALFA ROMEO 147 Halvkombi 2001>2009,3,Steinhof,A-035,23,,,Fast dragkrok,Passar 147,,Ja,1087,1087,1087,3474,2895,2316,https://example.com/install,,,,,,,Nej,,Fast dragkrok,Dragkrokar,1300 kg,60 kg,,Ja,"3,0 timmar",,5907615800962,Ja,,,7869,https://example.com/product\n',
        encoding="utf-8",
    )
    import_csv(csv_file, session)
    import_csv(csv_file, session)
    assert session.scalar(select(func.count()).select_from(Product)) == 1
    assert session.scalar(select(func.count()).select_from(ProductFitment)) == 1
