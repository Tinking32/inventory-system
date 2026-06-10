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
    request: Request,
    name: str = Form(...),
    quantity: int = Form(...),
    price: float = Form(...),
    low_stock_threshold: int = Form(20),
    category_id: str = Form(""),
    db: Session = Depends(get_db),
):
    cat_id = int(category_id) if category_id else None
    if cat_id and not db.get(Category, cat_id):
        categories = db.query(Category).order_by(Category.name).all()
        return templates.TemplateResponse(
            "add_item.html",
            {"request": request, "categories": categories, "error": f"Category not found."},
            status_code=400,
        )

    product = Product(
        name=name, quantity=quantity, price=price,
        low_stock_threshold=low_stock_threshold, category_id=cat_id,
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
    request: Request,
    name: str = Form(...),
    quantity: int = Form(...),
    price: float = Form(...),
    low_stock_threshold: int = Form(20),
    category_id: str = Form(""),
    db: Session = Depends(get_db),
):
    item = db.get(Product, product_id)
    if not item:
        return RedirectResponse(url="/", status_code=303)
    cat_id = int(category_id) if category_id else None
    item.name = name
    item.quantity = quantity
    item.price = price
    item.low_stock_threshold = low_stock_threshold
    item.category_id = cat_id
    db.commit()
    return RedirectResponse(url="/", status_code=303)


@router.get("/delete/{product_id}")
def delete_item(product_id: int, db: Session = Depends(get_db)):
    item = db.get(Product, product_id)
    if item:
        db.delete(item)
        db.commit()
    return RedirectResponse(url="/", status_code=303)


# ---- Categories management ----

@router.get("/categories")
def categories_page(request: Request, db: Session = Depends(get_db)):
    cats = db.query(Category).order_by(Category.name).all()
    return templates.TemplateResponse(
        "categories.html", {"request": request, "categories": cats}
    )


@router.post("/categories")
def add_category(
    request: Request,
    name: str = Form(..., min_length=1),
    db: Session = Depends(get_db),
):
    existing = db.query(Category).filter(Category.name == name.strip()).first()
    if existing:
        cats = db.query(Category).order_by(Category.name).all()
        return templates.TemplateResponse(
            "categories.html",
            {"request": request, "categories": cats, "error": f"Category '{name}' already exists."},
            status_code=400,
        )
    db.add(Category(name=name.strip()))
    db.commit()
    return RedirectResponse(url="/categories", status_code=303)


@router.post("/categories/{category_id}/delete")
def delete_category(
    category_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    cat = db.get(Category, category_id)
    if not cat:
        return RedirectResponse(url="/categories", status_code=303)

    # FK check: don't delete categories that have products
    product_count = db.query(Product).filter(Product.category_id == category_id).count()
    if product_count > 0:
        cats = db.query(Category).order_by(Category.name).all()
        return templates.TemplateResponse(
            "categories.html",
            {
                "request": request,
                "categories": cats,
                "error": f"Cannot delete '{cat.name}' — it has {product_count} product(s). Remove or reassign them first.",
            },
            status_code=400,
        )

    db.delete(cat)
    db.commit()
    return RedirectResponse(url="/categories", status_code=303)
