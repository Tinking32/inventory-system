from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session


from app.database import get_db
from app.models import Category, Product
from app.services.category_auto import suggest_category
from app.services.csv_import import execute_import, generate_sample_csv, parse_csv

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

    # Validate non-negative
    if quantity < 0 or price < 0 or low_stock_threshold < 0:
        categories = db.query(Category).order_by(Category.name).all()
        return templates.TemplateResponse(
            "add_item.html",
            {"request": request, "categories": categories, "error": "Quantity, price, and threshold must be >= 0."},
            status_code=400,
        )

    # Auto-detect category if none provided
    if not cat_id:
        suggested = suggest_category(name)
        if suggested:
            existing = db.query(Category).filter(Category.name == suggested).first()
            if existing:
                cat_id = existing.id

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


@router.post("/categories/{category_id}/edit")
def edit_category(
    category_id: int,
    request: Request,
    name: str = Form(..., min_length=1),
    db: Session = Depends(get_db),
):
    cat = db.get(Category, category_id)
    if not cat:
        return RedirectResponse(url="/categories", status_code=303)

    existing = db.query(Category).filter(Category.name == name.strip(), Category.id != category_id).first()
    if existing:
        cats = db.query(Category).order_by(Category.name).all()
        return templates.TemplateResponse(
            "categories.html",
            {"request": request, "categories": cats, "error": f"Category '{name}' already exists."},
            status_code=400,
        )

    cat.name = name.strip()
    db.commit()
    cats = db.query(Category).order_by(Category.name).all()
    return templates.TemplateResponse(
        "categories.html",
        {"request": request, "categories": cats, "ok": f"Category renamed to '{cat.name}'."},
    )


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


# ---- CSV Import ----

@router.get("/import")
def import_form(request: Request):
    sample = generate_sample_csv()
    return templates.TemplateResponse(
        "import.html", {"request": request, "sample": sample}
    )


@router.post("/import")
async def import_preview(request: Request, db: Session = Depends(get_db)):
    body = await request.form()
    file = body.get("file")
    if not file or not hasattr(file, "file"):
        return templates.TemplateResponse(
            "import.html",
            {"request": request, "sample": generate_sample_csv(), "error": "Please select a CSV file."},
        )

    content = (await file.read()).decode("utf-8", errors="replace")
    rows = parse_csv(content, db)
    valid_count = sum(1 for r in rows if r.valid)
    error_count = sum(1 for r in rows if not r.valid)

    return templates.TemplateResponse(
        "import.html",
        {
            "request": request,
            "sample": generate_sample_csv(),
            "rows": rows,
            "valid_count": valid_count,
            "error_count": error_count,
            "csv_content": content,
            "show_preview": True,
        },
    )


@router.post("/import/execute")
async def import_execute(request: Request, db: Session = Depends(get_db)):
    body = await request.form()
    csv_content = body.get("csv_content", "")
    content = csv_content if isinstance(csv_content, str) else str(csv_content)

    rows = parse_csv(content, db)
    imported = execute_import(rows, db)
    total = len(rows)

    return templates.TemplateResponse(
        "import.html",
        {
            "request": request,
            "sample": generate_sample_csv(),
            "imported": imported,
            "skipped": total - imported,
            "total": total,
            "import_done": True,
        },
    )
