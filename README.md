# Inventory Management System v2

REST API for product inventory tracking with natural language query support and JWT authentication. Built with FastAPI, SQLAlchemy, PostgreSQL, and Docker.

**Live:** [jiating-inventory-system.onrender.com](https://jiating-inventory-system.onrender.com)

---

## Architecture

```
Client (Bootstrap UI / Swagger / curl)
       │
       ▼
┌─────────────────────────────────┐
│  FastAPI App (Docker container) │
│  ┌──────────┐  ┌─────────────┐  │
│  │ Products │  │ /ask (mock)  │  │
│  │  CRUD    │  │ → keywords   │  │
│  │ JWT auth │  │ → SQL mapper │  │
│  └──────────┘  └─────────────┘  │
│         │              │         │
│    ┌────▼──────────────▼────┐    │
│    │   SQLAlchemy ORM       │    │
│    │   Alembic migrations   │    │
│    └───────────┬────────────┘    │
└────────────────┼─────────────────┘
                 │
        ┌────────▼────────┐
        │  PostgreSQL 16  │
        │  (or SQLite dev)│
        └─────────────────┘

Future: /ask endpoint swaps mock for LLM API microservice.
```

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/Tinking32/inventory-system.git
cd inventory-system

# 2. Install
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 3. Run (SQLite, zero config)
uvicorn app.main:app --reload

# 4. Open http://localhost:8000/docs
```

## Docker

```bash
# Edit .env: uncomment the PostgreSQL DATABASE_URL
docker-compose up --build
```

## API Endpoints

### Products

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/products/` | No | List with search, sort, paginate, low-stock filter |
| GET | `/api/products/{id}` | No | Single product |
| POST | `/api/products/` | JWT | Create |
| PUT | `/api/products/{id}` | JWT | Update |
| DELETE | `/api/products/{id}` | JWT | Delete |

### Categories

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/categories/` | No | List |
| POST | `/api/categories/` | No | Create |

### Natural Language Query

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/ask/` | No | Ask questions about inventory |

Example questions: "which products are low on stock?", "what is the total value of inventory?", "list all products in Electronics"

### Auth

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/register` | Create account |
| POST | `/api/auth/login` | Get access + refresh tokens |
| POST | `/api/auth/refresh` | Refresh access token |
| GET | `/api/auth/me` | Current user info |

## Tech Stack

- **Framework:** FastAPI 0.115
- **ORM:** SQLAlchemy 2.0
- **Migrations:** Alembic
- **Auth:** JWT (python-jose) + bcrypt
- **DB:** PostgreSQL 16 (production) / SQLite (development)
- **Tests:** pytest + httpx (28 tests, 100% pass)
- **Container:** Docker + docker-compose
- **CI/CD:** Render (from v1) — GitHub Actions (coming)

## Run Tests

```bash
pytest tests/ -v
```

## Project Structure

```
.
├── app/
│   ├── main.py              # FastAPI app entry
│   ├── config.py            # pydantic-settings
│   ├── database.py          # SQLAlchemy engine + session
│   ├── models/
│   │   └── models.py        # Product, Category, User
│   ├── schemas/
│   │   ├── product.py       # Pydantic CRUD schemas
│   │   ├── auth.py          # Auth schemas
│   │   └── ask.py           # Ask request/response
│   ├── routers/
│   │   ├── products.py      # Products CRUD
│   │   ├── categories.py    # Categories CRUD
│   │   ├── auth.py          # Register/login/refresh/me
│   │   └── ask.py           # Natural language query
│   └── services/
│       ├── auth.py          # Password hashing + JWT
│       └── ask_service.py   # Keyword → SQL mapper (mock LLM)
├── migrations/              # Alembic
├── tests/
│   ├── test_products.py     # 9 tests
│   ├── test_auth.py         # 9 tests
│   └── test_ask.py          # 10 tests
├── Dockerfile
├── docker-compose.yml
├── entrypoint.sh
└── requirements.txt
```
