from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Category, Product, User
from app.schemas.product import (
    ProductCreate,
    ProductListResponse,
    ProductResponse,
    ProductUpdate,
)
from app.services.auth import get_current_user

router = APIRouter(prefix="/api/products", tags=["products"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_or_create_category(db: Session, category_id: int | None) -> int | None:
    if category_id is None:
        return None
    cat = db.get(Category, category_id)
    if cat is None:
        raise HTTPException(
            status_code=404, detail=f"Category id={category_id} not found"
        )
    return category_id


# ---------------------------------------------------------------------------
# GET /api/products  — list with search, sort, pagination
# ---------------------------------------------------------------------------

@router.get("/", response_model=ProductListResponse)
def list_products(
    q: str | None = Query(default=None, description="Search by product name"),
    sort_by: str = Query(default="id", pattern=r"^(id|name|quantity|price|created_at)$"),
    order: str = Query(default="asc", pattern=r"^(asc|desc)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    category_id: int | None = Query(default=None),
    low_stock_only: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    query = db.query(Product)

    # Search
    if q:
        query = query.filter(Product.name.ilike(f"%{q}%"))

    # Category filter
    if category_id is not None:
        query = query.filter(Product.category_id == category_id)

    # Low stock filter
    if low_stock_only:
        query = query.filter(Product.quantity < Product.low_stock_threshold)

    # Sort
    sort_col = getattr(Product, sort_by)
    query = query.order_by(sort_col.desc() if order == "desc" else sort_col.asc())

    # Paginate
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return ProductListResponse(items=items, total=total, page=page, page_size=page_size)


# ---------------------------------------------------------------------------
# GET /api/products/{id}  — single product
# ---------------------------------------------------------------------------

@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


# ---------------------------------------------------------------------------
# POST /api/products  — create
# ---------------------------------------------------------------------------

@router.post("/", response_model=ProductResponse, status_code=201)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    _get_or_create_category(db, payload.category_id)
    product = Product(**payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


# ---------------------------------------------------------------------------
# PUT /api/products/{id}  — update
# ---------------------------------------------------------------------------

@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    if payload.category_id is not None:
        _get_or_create_category(db, payload.category_id)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return product


# ---------------------------------------------------------------------------
# DELETE /api/products/{id}  — delete (hard)
# ---------------------------------------------------------------------------

@router.delete("/{product_id}", status_code=204)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
    return None
