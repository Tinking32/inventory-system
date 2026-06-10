"""
Natural language query service.

Mock mode: keyword matching → SQL query.
LLM mode (future): generates SQL from NL via LLM API.

The interface contract is identical — swap the implementation, not the contract.
"""

from dataclasses import dataclass, field

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Category, Product


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
            "id": p.id,
            "name": p.name,
            "quantity": p.quantity,
            "price": p.price,
            "category": p.category.name if p.category else None,
            "is_low_stock": p.is_low_stock,
        }
        for p in products
    ]


def _match_keywords(question: str) -> str | None:
    """Return a canonical query_type based on keyword matching."""
    q = question.lower()

    # Check for category names FIRST — more specific than "list"
    # (The caller will re-check this if we return "smart_search")

    if any(w in q for w in ("low stock", "low on stock", "running low", "almost out", "库存不足", "快过期")):
        return "low_stock"
    if any(w in q for w in ("most expensive", "highest price", "priciest", "最贵")):
        return "most_expensive"
    if any(w in q for w in ("cheapest", "lowest price", "最便宜")):
        return "cheapest"
    if any(w in q for w in ("total value", "total worth", "total inventory", "总价值", "总值")):
        return "total_value"
    if any(w in q for w in ("how many", "count", "number of", "多少", "几个")):
        return "count"

    return "smart_search"


def process_question(question: str, db: Session) -> AskResult:
    """Main entry point. Routes to the right query handler based on keywords."""

    result = AskResult(question=question, query_type="unknown")
    query_type = _match_keywords(question)
    result.query_type = query_type

    if query_type == "low_stock":
        products = (
            db.query(Product)
            .filter(Product.quantity < Product.low_stock_threshold)
            .all()
        )
        result.query_type = "low_stock"
        result.results = _format_products(products)
        names = ", ".join(p["name"] for p in result.results)
        result.response_text = (
            f"{len(products)} product(s) below stock threshold: {names}."
            if products
            else "All products are above their stock thresholds."
        )

    elif query_type == "most_expensive":
        product = db.query(Product).order_by(Product.price.desc()).first()
        result.query_type = "most_expensive"
        if product:
            result.results = _format_products([product])
            result.response_text = (
                f"The most expensive product is {product.name} at ${product.price:.2f}."
            )

    elif query_type == "cheapest":
        product = db.query(Product).order_by(Product.price.asc()).first()
        result.query_type = "cheapest"
        if product:
            result.results = _format_products([product])
            result.response_text = (
                f"The cheapest product is {product.name} at ${product.price:.2f}."
            )

    elif query_type == "total_value":
        total = db.query(func.sum(Product.quantity * Product.price)).scalar() or 0
        count = db.query(Product).count()
        result.query_type = "total_value"
        result.results = [{"total_value": round(float(total), 2), "product_count": count}]
        result.response_text = (
            f"Total inventory value: ${total:,.2f} across {count} product(s)."
        )

    elif query_type == "count":
        total = db.query(Product).count()
        result.query_type = "count"
        result.results = [{"total_products": total}]
        result.response_text = f"There are {total} product(s) in the inventory."

    elif query_type == "smart_search":
        q = question.lower()

        # 1. Try to match a category name first
        for cat in db.query(Category).all():
            if cat.name.lower() in q:
                products = (
                    db.query(Product)
                    .filter(Product.category_id == cat.id)
                    .all()
                )
                result.query_type = "category_filter"
                result.results = _format_products(products)
                result.response_text = (
                    f"Found {len(products)} product(s) in '{cat.name}'."
                )
                return result

        # 2. Explicit list/show request → list all
        if any(w in q for w in ("list", "show", "列出", "显示", "all")):
            products = db.query(Product).order_by(Product.name).all()
            result.query_type = "list_all"
            result.results = _format_products(products)
            result.response_text = f"Showing all {len(products)} product(s)."
            return result

        # 3. Fallback: name search with stopword filtering
        stopwords = {
            "find", "search", "look", "for", "the", "a", "an", "is", "in",
            "on", "at", "get", "me", "show", "list", "all", "what", "which",
            "are", "there", "any", "many", "much", "how", "products", "product",
        }
        words = [w for w in question.split() if w.lower() not in stopwords and len(w) > 1]
        search_word = max(words, key=len) if words else (question.split()[-1] if question.split() else "")
        products = (
            db.query(Product)
            .filter(Product.name.ilike(f"%{search_word}%"))
            .all()
        )
        result.query_type = "name_search"
        result.results = _format_products(products)
        result.response_text = (
            f"Found {len(products)} product(s) matching '{search_word}'."
            if products
            else f"No products found matching '{search_word}'."
        )

    return result
