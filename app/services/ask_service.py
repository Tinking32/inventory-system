"""
Natural language query service.

Mock mode: keyword matching → SQL query.
LLM mode (future): generates SQL from NL via LLM API.
"""

from dataclasses import dataclass, field

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Category, Product

# Words that should never be treated as product names
STOPWORDS = {
    "find", "search", "look", "for", "the", "a", "an", "is", "in", "on",
    "at", "get", "me", "show", "list", "all", "what", "which", "are",
    "there", "any", "many", "much", "how", "products", "product",
    "quantity", "qty", "stock", "price", "cost", "expensive", "cheap",
    "cheapest", "low", "high", "total", "value", "worth", "inventory",
    "do", "we", "have", "tell", "about", "info", "detail", "details",
    "of", "the", "please", "can", "you", "i", "need", "want", "know",
    "does", "has", "available", "current", "now", "left", "remaining",
}


@dataclass
class AskResult:
    question: str
    query_type: str
    results: list[dict] = field(default_factory=list)
    response_text: str = ""
    mode: str = "mock"


def _format_products(products: list[Product]) -> list[dict]:
    return [
        {
            "id": p.id, "name": p.name,
            "quantity": p.quantity, "price": p.price,
            "category": p.category.name if p.category else None,
            "is_low_stock": p.is_low_stock,
            "low_stock_threshold": p.low_stock_threshold,
        }
        for p in products
    ]


def _find_product(question: str, db: Session) -> Product | None:
    """Try to find a product by name from the question text."""
    words = [w for w in question.split() if w.lower() not in STOPWORDS and len(w) > 1]

    # Try progressively shorter word combinations
    for n in range(min(len(words), 4), 0, -1):
        for i in range(len(words) - n + 1):
            phrase = " ".join(words[i:i + n])
            product = db.query(Product).filter(
                Product.name.ilike(f"%{phrase}%")
            ).first()
            if product:
                return product
    return None


def _detect_intent(question: str, found_product: bool) -> str:
    """Return the intent type based on keywords."""
    q = question.lower()

    if found_product:
        # Price first (more specific patterns win)
        if any(w in q for w in ("price", "cost", "how much does", "worth of")):
            return "product_price"
        if any(w in q for w in ("how many", "how much", "quantity", "qty", "stock level", "stock of", "in stock")):
            return "product_quantity"
        if any(w in q for w in ("low", "running out", "almost out", "enough", "库存", "快过期")):
            return "product_low_stock"

    # Aggregate intents
    if any(w in q for w in ("low stock", "low on stock", "running low", "almost out", "库存不足", "快过期")):
        return "low_stock"
    if any(w in q for w in ("most expensive", "highest price", "priciest", "最贵")):
        return "most_expensive"
    if any(w in q for w in ("cheapest", "lowest price", "最便宜")):
        return "cheapest"
    if any(w in q for w in ("total value", "total worth", "total inventory", "总价值", "总值")):
        return "total_value"
    if any(w in q for w in ("how many products", "count products", "number of products", "total products", "几个产品", "多少产品")):
        return "count"

    return "smart_search"


def process_question(question: str, db: Session) -> AskResult:
    """Main entry point. Extract product → detect intent → route to handler."""

    result = AskResult(question=question, query_type="unknown")

    # Step 1: Try to find a product mentioned in the question
    product = _find_product(question, db)

    # Step 2: Detect intent
    intent = _detect_intent(question, product is not None)
    result.query_type = intent

    # ---- Product-specific handlers ----

    if product and intent == "product_quantity":
        result.results = _format_products([product])
        result.response_text = (
            f"{product.name} has {product.quantity} units in stock"
            f"{' (threshold: ' + str(product.low_stock_threshold) + ')' if product.quantity < product.low_stock_threshold else ''}."
        )
        return result

    if product and intent == "product_price":
        result.results = _format_products([product])
        result.response_text = f"{product.name} costs ${product.price:.2f} per unit."
        return result

    if product and intent == "product_low_stock":
        result.results = _format_products([product])
        if product.is_low_stock:
            result.response_text = (
                f"Yes, {product.name} is LOW — only {product.quantity} units left "
                f"(threshold: {product.low_stock_threshold})."
            )
        else:
            result.response_text = (
                f"No, {product.name} has {product.quantity} units "
                f"(threshold: {product.low_stock_threshold})."
            )
        return result

    if product and intent == "smart_search":
        # Found product, no specific intent → show product detail
        result.query_type = "product_detail"
        result.results = _format_products([product])
        result.response_text = (
            f"📦 {product.name} | Qty: {product.quantity} | Price: ${product.price:.2f} | "
            f"Category: {product.category.name if product.category else 'None'} | "
            f"Status: {'⚠️ Low Stock' if product.is_low_stock else '✅ In Stock'}"
        )
        return result

    # ---- Aggregate handlers ----

    if intent == "low_stock":
        products = (
            db.query(Product)
            .filter(Product.quantity < Product.low_stock_threshold)
            .all()
        )
        result.results = _format_products(products)
        names = ", ".join(p["name"] for p in result.results)
        result.response_text = (
            f"{len(products)} product(s) below threshold: {names}."
            if products
            else "All products are above their stock thresholds."
        )
        return result

    if intent == "most_expensive":
        p = db.query(Product).order_by(Product.price.desc()).first()
        if p:
            result.results = _format_products([p])
            result.response_text = f"The most expensive product is {p.name} at ${p.price:.2f}."
        return result

    if intent == "cheapest":
        p = db.query(Product).order_by(Product.price.asc()).first()
        if p:
            result.results = _format_products([p])
            result.response_text = f"The cheapest product is {p.name} at ${p.price:.2f}."
        return result

    if intent == "total_value":
        total = db.query(func.sum(Product.quantity * Product.price)).scalar() or 0
        count = db.query(Product).count()
        result.results = [{"total_value": round(float(total), 2), "product_count": count}]
        result.response_text = f"Total inventory value: ${total:,.2f} across {count} product(s)."
        return result

    if intent == "count":
        total = db.query(Product).count()
        result.results = [{"total_products": total}]
        result.response_text = f"There are {total} product(s) in the inventory."
        return result

    # ---- Smart search fallback ----
    # (no product found, no aggregate intent)

    q = question.lower()

    # Category filter
    for cat in db.query(Category).all():
        if cat.name.lower() in q:
            products = db.query(Product).filter(Product.category_id == cat.id).all()
            result.query_type = "category_filter"
            result.results = _format_products(products)
            result.response_text = f"Found {len(products)} product(s) in '{cat.name}'."
            return result

    # List all
    if any(w in q for w in ("list", "show", "列出", "显示", "all products", "everything")):
        products = db.query(Product).order_by(Product.name).all()
        result.query_type = "list_all"
        result.results = _format_products(products)
        result.response_text = f"Showing all {len(products)} product(s)."
        return result

    # Name search
    words = [w for w in question.split() if w.lower() not in STOPWORDS and len(w) > 1]
    search_word = max(words, key=len) if words else (question.split()[-1] if question.split() else "")
    products = db.query(Product).filter(Product.name.ilike(f"%{search_word}%")).all()
    result.query_type = "name_search"
    result.results = _format_products(products)
    result.response_text = (
        f"Found {len(products)} product(s) matching '{search_word}'."
        if products
        else f"No products found matching '{search_word}'. Try a different search term."
    )
    return result
