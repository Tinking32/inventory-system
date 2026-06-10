"""Seed the database with realistic B2B inventory data."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal, engine, Base
from app.models import Category, Product

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# Clear existing
db.query(Product).delete()
db.query(Category).delete()
db.commit()

# Categories
cats = {
    "Electronics": Category(name="Electronics",
        description="Computer peripherals, displays, and accessories"),
    "Beverages": Category(name="Beverages",
        description="Drinks, refreshments, and bottled beverages"),
    "Office Supplies": Category(name="Office Supplies",
        description="Stationery, paper, and office consumables"),
    "Food & Snacks": Category(name="Food & Snacks",
        description="Packaged food, snacks, and pantry items"),
}
for c in cats.values():
    db.add(c)
db.commit()

# Products per category
products = [
    # Electronics (cat 1)
    ("Dell Monitor 24\"", "24-inch 1080p IPS monitor, HDMI+DP", 5, 299.00, 10, 1),
    ("Logitech MX Mouse", "Wireless ergonomic mouse, USB-C", 20, 89.90, 10, 1),
    ("AA Batteries (Box)", "Pack of 24 AA alkaline batteries", 250, 15.50, 50, 1),
    ("USB-C Hub 7-in-1", "HDMI, USB-A x3, SD card, PD 100W", 35, 45.00, 15, 1),

    # Beverages (cat 2)
    ("Coca Cola (Carton)", "24 x 330ml cans", 150, 12.90, 30, 2),
    ("Milo Tin 1.5kg", "Malted chocolate drink powder", 3, 9.50, 10, 2),
    ("Nescafe Gold (Jar)", "200g instant coffee", 42, 14.80, 12, 2),
    ("Evian Water (Pack)", "12 x 500ml bottles", 88, 8.90, 24, 2),

    # Office Supplies (cat 3)
    ("A4 Paper (Carton)", "5 reams, 500 sheets each, 80gsm", 60, 28.00, 10, 3),
    ("Ballpoint Pen (Box)", "Box of 50 blue ballpoint pens", 120, 8.50, 30, 3),
    ("Sticky Notes (Pack)", "12 pads, 100 sheets each, assorted", 75, 6.20, 20, 3),

    # Food & Snacks (cat 4)
    ("Instant Noodles (Carton)", "24 packs, chicken flavor", 40, 10.80, 15, 4),
    ("Digestive Biscuits (Box)", "12 x 250g packs", 55, 4.50, 20, 4),
    ("Mixed Nuts (Bag)", "1kg roasted mixed nuts", 18, 16.90, 10, 4),
]
for name, desc, qty, price, threshold, cat_id in products:
    db.add(Product(name=name, description=desc, quantity=qty, price=price,
                   low_stock_threshold=threshold, category_id=cat_id))

db.commit()
print(f"Seeded: {db.query(Category).count()} categories, {db.query(Product).count()} products")
db.close()
