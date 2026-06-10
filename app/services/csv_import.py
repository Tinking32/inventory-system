"""CSV import service — parse, validate, and import products."""

import csv
import io
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.models import Category, Product
from app.services.category_auto import suggest_category


@dataclass
class CsvRow:
    row_num: int
    name: str = ""
    description: str = ""
    quantity: int = 0
    price: float = 0.0
    low_stock_threshold: int = 20
    category_name: str = ""
    errors: list[str] = field(default_factory=list)
    valid: bool = True


def parse_csv(content: str, db: Session) -> list[CsvRow]:
    """Parse CSV content and validate each row."""
    reader = csv.DictReader(io.StringIO(content))
    rows: list[CsvRow] = []
    seen_names: set[str] = set()

    # Build category lookup
    categories = {c.name.lower(): c for c in db.query(Category).all()}

    for i, row_dict in enumerate(reader, start=1):
        r = CsvRow(row_num=i)

        # Name (required)
        r.name = (row_dict.get("name") or "").strip()
        if not r.name:
            r.errors.append("Product name is required")
            r.valid = False
        elif r.name.lower() in seen_names:
            r.errors.append(f"Duplicate name in CSV: '{r.name}'")
            r.valid = False
        else:
            seen_names.add(r.name.lower())

        # Description (optional)
        r.description = (row_dict.get("description") or "").strip()

        # Quantity (required, >= 0)
        qty_str = (row_dict.get("quantity") or "").strip()
        try:
            r.quantity = int(qty_str)
            if r.quantity < 0:
                r.errors.append("Quantity must be >= 0")
                r.valid = False
        except (ValueError, TypeError):
            r.errors.append(f"Invalid quantity: '{qty_str}'")
            r.valid = False

        # Price (required, >= 0)
        price_str = (row_dict.get("price") or "").strip()
        try:
            r.price = float(price_str)
            if r.price < 0:
                r.errors.append("Price must be >= 0")
                r.valid = False
        except (ValueError, TypeError):
            r.errors.append(f"Invalid price: '{price_str}'")
            r.valid = False

        # Low stock threshold (optional)
        threshold_str = (row_dict.get("low_stock_threshold") or "20").strip()
        try:
            r.low_stock_threshold = int(threshold_str)
        except (ValueError, TypeError):
            r.low_stock_threshold = 20

        # Category (optional, auto-detect if missing)
        r.category_name = (row_dict.get("category") or "").strip()
        if not r.category_name:
            suggested = suggest_category(r.name)
            r.category_name = suggested or ""
        elif r.category_name.lower() not in categories:
            r.errors.append(f"Unknown category: '{r.category_name}'")
            r.valid = False

        rows.append(r)

    return rows


def execute_import(rows: list[CsvRow], db: Session) -> int:
    """Import valid rows into the database. Returns count of imported products."""
    categories = {c.name.lower(): c for c in db.query(Category).all()}
    count = 0

    for r in rows:
        if not r.valid:
            continue

        # Get or create category
        cat_key = r.category_name.lower()
        cat = categories.get(cat_key)
        if not cat and r.category_name:
            cat = Category(name=r.category_name.strip())
            db.add(cat)
            db.flush()
            categories[cat_key] = cat

        # Check for duplicate in DB
        existing = db.query(Product).filter(Product.name == r.name).first()
        if existing:
            r.errors.append(f"Already exists in database: '{r.name}'")
            r.valid = False
            continue

        db.add(Product(
            name=r.name,
            description=r.description,
            quantity=r.quantity,
            price=r.price,
            low_stock_threshold=r.low_stock_threshold,
            category_id=cat.id if cat else None,
        ))
        count += 1

    db.commit()
    return count


def generate_sample_csv() -> str:
    """Generate a sample CSV file for download."""
    return (
        "name,description,quantity,price,low_stock_threshold,category\n"
        'Wireless Keyboard,Ergonomic mechanical,50,89.90,10,Electronics\n'
        'Green Tea Box,20 tea bags,120,5.50,20,Beverages\n'
        "Notebook A5,200-page ruled notebook,75,3.99,15,Office Supplies\n"
        'Protein Bar Box,12 bars chocolate,90,24.00,10,Food & Snacks\n'
    )
