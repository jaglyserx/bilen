"""Idempotent importer for the Bilen & Jag catalogue CSV export."""

import argparse
import csv
import re
import tempfile
import unicodedata
import urllib.request
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import (
    Category,
    ImportRow,
    ImportRun,
    Inventory,
    Manufacturer,
    Price,
    Product,
    ProductFitment,
    ProductIdentifier,
    ProductLink,
    Vehicle,
)

SHEET_URL = "https://docs.google.com/spreadsheets/d/1xwqu0iQk-aS8ssIBvr6b8tRaTlgKdce2qYli-AU0Sgo/export?format=csv&gid=462267230"
INVALID = {"", "#n/a", "#ref!", "n/a", "-"}


def clean(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.replace("\xa0", " ").strip()
    return None if value.casefold() in INVALID else value


def normalize(value: str | None) -> str:
    value = clean(value) or ""
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def slugify(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")


def decimal_value(value: str | None) -> Decimal | None:
    value = clean(value)
    if not value or value.casefold() == "utgått":
        return None
    match = re.search(r"-?[\d\s.]+(?:,\d+)?", value)
    if not match:
        return None
    normalized = match.group().replace(" ", "").replace(".", "").replace(",", ".")
    try:
        return Decimal(normalized)
    except InvalidOperation:
        return None


def integer_value(value: str | None) -> int | None:
    number = decimal_value(value)
    return int(number) if number is not None else None


def boolean_value(value: str | None) -> bool | None:
    value = (clean(value) or "").casefold()
    if value in {"ja", "yes", "true", "1"}:
        return True
    if value in {"nej", "no", "false", "0"}:
        return False
    return None


def parse_minutes(value: str | None) -> int | None:
    hours = decimal_value(value)
    return round(hours * 60) if hours is not None else None


def parse_vehicle(label: str, legacy_id: str | None, category: str | None = None) -> dict:
    text = clean(label) or "Okänt fordon"
    year_match = re.search(r"((?:19|20)\d{2})\s*[>/\-]\s*((?:19|20)\d{2})", text)
    category_parts = [clean(part) for part in (category or "").split(",")]
    make = category_parts[1] if len(category_parts) > 1 else None
    make = make or (text.split(maxsplit=1)[0] if text else None)
    without_make = text[len(make) :].strip() if make else text
    model = re.split(r"\s+(?:19|20)\d{2}", without_make, maxsplit=1)[0].strip() or None
    return {
        "source_label": text,
        "normalized_label": normalize(text),
        "legacy_model_id": clean(legacy_id),
        "make": make.title() if make else None,
        "model": model,
        "body_style": None,
        "year_from": int(year_match.group(1)) if year_match else None,
        "year_to": int(year_match.group(2)) if year_match else None,
    }


def first_or_create(session: Session, model, defaults=None, **lookup):
    instance = session.scalar(select(model).filter_by(**lookup))
    if instance:
        return instance, False
    instance = model(**lookup, **(defaults or {}))
    session.add(instance)
    session.flush()
    return instance, True


def set_price(session: Session, product: Product, kind: str, raw: str | None, vat: bool):
    amount = decimal_value(raw)
    if amount is None:
        return
    price = session.scalar(
        select(Price).filter_by(product_id=product.id, kind=kind, currency="SEK")
    )
    if price is None:
        price = Price(
            product_id=product.id, kind=kind, currency="SEK", amount=amount, vat_included=vat
        )
        session.add(price)
    else:
        price.amount, price.vat_included = amount, vat


def set_inventory(session: Session, product: Product, location: str, raw: str | None):
    value = clean(raw)
    if value is None:
        return
    inventory, _ = first_or_create(session, Inventory, product_id=product.id, location=location)
    inventory.quantity = integer_value(value)
    inventory.availability = value if inventory.quantity is None else None


def set_link(session: Session, product: Product, kind: str, raw: str | None):
    url = clean(raw)
    if url and url.startswith(("http://", "https://")):
        first_or_create(session, ProductLink, product_id=product.id, kind=kind, url=url)


def import_csv(path: Path, session: Session) -> ImportRun:
    run = ImportRun(source=str(path))
    session.add(run)
    session.flush()
    with path.open(encoding="utf-8-sig", newline="") as source:
        rows = csv.reader(source)
        next(rows, None)  # sheet metadata row
        headings = next(rows)
        for row_number, values in enumerate(rows, start=3):
            values += [""] * (len(headings) - len(values))
            raw = dict(zip(headings, values, strict=False))
            raw["Bilmodell"] = values[0]
            manufacturer_name = clean(values[2])
            article_number = clean(values[3])
            if not manufacturer_name or not article_number:
                run.skipped += 1
                run.warnings += 1
                session.add(
                    ImportRow(
                        import_run_id=run.id,
                        row_number=row_number,
                        status="skipped",
                        message="Missing manufacturer or article number",
                        raw_data=raw,
                    )
                )
                continue
            try:
                manufacturer, _ = first_or_create(
                    session,
                    Manufacturer,
                    normalized_name=normalize(manufacturer_name),
                    defaults={"name": manufacturer_name},
                )
                product, created = first_or_create(
                    session,
                    Product,
                    manufacturer_id=manufacturer.id,
                    normalized_article_number=normalize(article_number),
                    defaults={"article_number": article_number},
                )
                product.article_number = article_number
                identifier, _ = first_or_create(
                    session,
                    ProductIdentifier,
                    kind="article_number",
                    normalized_value=normalize(article_number),
                    defaults={"product_id": product.id, "value": article_number},
                )
                identifier.value = article_number
                product.name = clean(values[26]) or product.name
                product.towbar_type = clean(values[7]) or product.towbar_type
                product.description = clean(values[8]) or product.description
                product.internal_notes = clean(values[9]) or product.internal_notes
                product.webshop_visible = boolean_value(values[10]) or False
                product.status = (
                    "discontinued"
                    if any((clean(v) or "").casefold() == "utgått" for v in values[11:17])
                    else "active"
                )
                product.max_towing_weight_kg = (
                    decimal_value(values[28]) or product.max_towing_weight_kg
                )
                product.max_ball_weight_kg = decimal_value(values[29]) or product.max_ball_weight_kg
                product.weight_kg = decimal_value(values[30]) or product.weight_kg
                product.cutout_required = boolean_value(values[31])
                product.installation_minutes = (
                    parse_minutes(values[32]) or product.installation_minutes
                )
                product.ean = clean(values[34]) or product.ean
                product.lockable = boolean_value(values[35])
                product.size = clean(values[36]) or product.size
                product.woocommerce_id = clean(values[38]) or product.woocommerce_id
                product.webshop_url = clean(values[39]) or product.webshop_url

                vehicle_data = parse_vehicle(values[0], values[1], values[27])
                vehicle, _ = first_or_create(
                    session,
                    Vehicle,
                    normalized_label=vehicle_data.pop("normalized_label"),
                    defaults=vehicle_data,
                )
                notes = clean(values[8]) or ""
                fitment, _ = first_or_create(
                    session,
                    ProductFitment,
                    product_id=product.id,
                    vehicle_id=vehicle.id,
                    fitment_notes=notes,
                )
                fitment.electrical_connection = clean(values[33])
                fitment.camper_van_notes = clean(values[24])

                for kind, index, vat in (
                    ("purchase", 11, False),
                    ("retail_ex_vat", 16, False),
                    ("retail_inc_vat", 15, True),
                ):
                    set_price(session, product, kind, values[index], vat)
                for location, index in (("Steinhof", 4), ("Borås", 5), ("Other", 6)):
                    set_inventory(session, product, location, values[index])
                set_link(session, product, "installation", values[17])
                set_link(session, product, "wiring", values[19])
                set_link(session, product, "webshop", values[39])

                for category_name in [clean(part) for part in values[27].split(",")]:
                    if category_name:
                        category, _ = first_or_create(
                            session,
                            Category,
                            slug=slugify(category_name),
                            defaults={"name": category_name},
                        )
                        if category not in product.categories:
                            product.categories.append(category)
                run.inserted += int(created)
                run.updated += int(not created)
                session.add(
                    ImportRow(
                        import_run_id=run.id, row_number=row_number, status="imported", raw_data=raw
                    )
                )
                if row_number % 500 == 0:
                    session.flush()
            except Exception as exc:
                run.skipped += 1
                run.warnings += 1
                session.add(
                    ImportRow(
                        import_run_id=run.id,
                        row_number=row_number,
                        status="error",
                        message=str(exc),
                        raw_data=raw,
                    )
                )
    run.status = "completed"
    run.finished_at = datetime.now(UTC)
    session.commit()
    return run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_file", nargs="?", type=Path)
    parser.add_argument(
        "--sheet",
        action="store_true",
        help="Download and import the configured Google Sheet CSV export",
    )
    args = parser.parse_args()
    if args.sheet:
        with tempfile.TemporaryDirectory() as directory:
            csv_file = Path(directory) / "catalogue.csv"
            urllib.request.urlretrieve(SHEET_URL, csv_file)  # noqa: S310
            run_import(csv_file)
        return
    if args.csv_file is None:
        parser.error("provide a CSV file or use --sheet")
    if not args.csv_file.exists():
        parser.error(f"File does not exist: {args.csv_file}")
    run_import(args.csv_file)


def run_import(csv_file: Path) -> None:
    with SessionLocal() as session:
        run = import_csv(csv_file, session)
    print(
        f"Import complete: {run.inserted} inserted, {run.updated} updated, "
        f"{run.skipped} skipped, {run.warnings} warnings"
    )


if __name__ == "__main__":
    main()
