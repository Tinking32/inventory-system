from fastapi import FastAPI

from app.routers import ask, auth, categories, frontend, products

app = FastAPI(
    title="Inventory Management System",
    description="REST API for product inventory tracking with natural language query support.",
    version="2.0.0",
)

# Routers
# Frontend routes first (/, /add, /edit, /delete)
app.include_router(frontend.router)
# API routes
app.include_router(auth.router)
app.include_router(ask.router)
app.include_router(products.router)
app.include_router(categories.router)


@app.get("/")
def read_root():
    return {"msg": "Inventory Management System v2 — running"}


@app.get("/check_health")
def check_health():
    return {"status": "healthy"}
