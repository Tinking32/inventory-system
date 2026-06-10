from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Category, Product

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(tags=["frontend"])


@router.get("/")
def dashboard(
    request: Request,
    q: str | None = None,
    sort_by: str = "id",
    order: str = "asc",
    db: Session = Depends(get_db),
):
    query = db.query(Product)
    if q:
        query = query.filter(Product.name.ilike(f"%{q}%"))

    sort_col = getattr(Product, sort_by, Product.id)
    query = query.order_by(sort_col.desc() if order == "desc" else sort_col.asc())
    items = query.all()

    return templates.TemplateResponse(
        "index.html",
        {"request": request, "items": items, "query": q or "", "sort_by": sort_by, "order": order},
    )


@router.get("/add")
def add_form(request: Request, db: Session = Depends(get_db)):
    categories = db.query(Category).order_by(Category.name).all()
    return templates.TemplateResponse(
        "add_item.html", {"request": request, "categories": categories}
    )


@router.post("/add")
def add_item(
    name: str = Form(...),
    quantity: int = Form(...),
    price: float = Form(...),
    low_stock_threshold: int = Form(20),
    category_id: int | None = Form(None),
    db: Session = Depends(get_db),
):
    product = Product(
        name=name,
        quantity=quantity,
        price=price,
        low_stock_threshold=low_stock_threshold,
        category_id=category_id if category_id else None,
    )
    db.add(product)
    db.commit()
    return RedirectResponse(url="/", status_code=303)


@router.get("/edit/{product_id}")
def edit_form(product_id: int, request: Request, db: Session = Depends(get_db)):
    item = db.get(Product, product_id)
    if not item:
        return RedirectResponse(url="/", status_code=303)
    categories = db.query(Category).order_by(Category.name).all()
    return templates.TemplateResponse(
        "edit_item.html", {"request": request, "item": item, "categories": categories}
    )


@router.post("/edit/{product_id}")
def edit_item(
    product_id: int,
    name: str = Form(...),
    quantity: int = Form(...),
    price: float = Form(...),
    low_stock_threshold: int = Form(20),
    category_id: int | None = Form(None),
    db: Session = Depends(get_db),
):
    item = db.get(Product, product_id)
    if not item:
        return RedirectResponse(url="/", status_code=303)
    item.name = name
    item.quantity = quantity
    item.price = price
    item.low_stock_threshold = low_stock_threshold
    item.category_id = category_id if category_id else None
    db.commit()
    return RedirectResponse(url="/", status_code=303)


@router.get("/delete/{product_id}")
def delete_item(product_id: int, db: Session = Depends(get_db)):
    item = db.get(Product, product_id)
    if item:
        db.delete(item)
        db.commit()
    return RedirectResponse(url="/", status_code=303)
