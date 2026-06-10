# Inventory System v2 — Project Status

> Last updated: 2026-06-10
> Live: https://inventory-system-v2-11mj.onrender.com
> Repo: https://github.com/Tinking32/inventory-system (branch: `v2`)

---

## 已实现功能 (What's Built)

### 后端 API (Backend)

| 模块 | 端点 | 方法 | 说明 |
|------|------|------|------|
| Products | `/api/products/` | GET | 列表：搜索、排序、分页、分类筛选、低库存筛选 |
| Products | `/api/products/{id}` | GET | 单产品详情 |
| Products | `/api/products/` | POST | 创建（需 JWT） |
| Products | `/api/products/{id}` | PUT | 更新（需 JWT） |
| Products | `/api/products/{id}` | DELETE | 删除（需 JWT） |
| Categories | `/api/categories/` | GET | 列表 |
| Categories | `/api/categories/` | POST | 创建 |
| Categories | `/api/categories/{id}` | DELETE | 删除 |
| Ask AI | `/api/ask/` | POST | 自然语言查询（mock 模式，关键词匹配） |
| Auth | `/api/auth/register` | POST | 注册 |
| Auth | `/api/auth/login` | POST | 登录，获取 access + refresh token |
| Auth | `/api/auth/refresh` | POST | 刷新 token |
| Auth | `/api/auth/me` | GET | 当前用户信息 |
| Docs | `/docs` | GET | Swagger UI 自动生成 |
| Health | `/check_health` | GET | 健康检查 |

### 前端页面 (Frontend)

| 页面 | URL | 功能 |
|------|-----|------|
| Dashboard | `/` | Chart.js 柱状图 + 搜索 + 产品表格 + 🔍 Ask AI 聚焦搜索栏 |
| Add Item | `/add` | 添加产品表单（分类下拉、低库存阈值、错误行内提示） |
| Edit Item | `/edit/{id}` | 编辑产品表单 |
| Categories | `/categories` | 分类管理：添加、✏️行内改名、🗑️删除（FK 保护） |

### Ask AI 能力 (Natural Language Query)

| 问题类型 | 示例 | 回复 |
|---------|------|------|
| 产品数量查询 | "how many Dell Monitors do we have?" | "Dell Monitor has 5 units in stock" |
| 产品价格查询 | "what is the price of Logitech Mouse?" | "Logitech Mouse costs $29.99 per unit" |
| 产品低库存查询 | "is Coca Cola low on stock?" | "No, Coca Cola has 150 units" |
| 低库存汇总 | "which products are low on stock?" | 列出所有低于阈值的商品 |
| 最贵商品 | "what is the most expensive product?" | 返回价格最高的商品 |
| 库存总值 | "total value of inventory" | "$X,XXX.XX across Y products" |
| 分类筛选 | "list products in Electronics" | 返回该分类下所有商品 |
| 产品详情 | "tell me about Logitech Mouse" | 完整产品信息卡片 |
| 中文支持 | "哪些货库存不足？" | 同上 low_stock 查询 |

---

## 架构 (Architecture)

```
inventory-system-v2/
├── app/
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # pydantic-settings（环境变量配置）
│   ├── database.py          # SQLAlchemy 引擎 + get_db 依赖（SQLite/PostgreSQL 切换）
│   ├── models/
│   │   └── models.py        # Category, Product, User（FK 关系）
│   ├── schemas/
│   │   ├── product.py       # Pydantic CRUD schema
│   │   ├── auth.py          # Auth schema
│   │   └── ask.py           # Ask request/response
│   ├── routers/
│   │   ├── frontend.py      # 前端页面路由（/, /add, /edit, /categories）
│   │   ├── products.py      # 产品 CRUD API（POST/PUT/DELETE 需 JWT）
│   │   ├── categories.py    # 分类 API
│   │   ├── auth.py          # 注册/登录/刷新/me
│   │   └── ask.py           # POST /api/ask
│   ├── services/
│   │   ├── auth.py          # bcrypt 密码哈希 + JWT 令牌
│   │   └── ask_service.py   # 关键词匹配 → SQL（mock LLM 模式）
│   └── templates/           # Jinja2 模板（Bootstrap 5 + Chart.js）
├── tests/
│   ├── conftest.py          # TestClient + 内存 SQLite + auth 覆盖
│   ├── test_products.py     # 9 tests
│   ├── test_auth.py         # 9 tests
│   └── test_ask.py          # 10 tests
├── migrations/              # Alembic 自动生成
├── Dockerfile               # python:3.11-slim + 非 root 用户
├── docker-compose.yml       # app + PostgreSQL 16
├── entrypoint.sh            # 启动时自动 alembic upgrade head
├── render.yaml              # Render Blueprint（自动部署）
└── requirements.txt
```

**部署架构:**

```
Browser → Render (Docker) → FastAPI → PostgreSQL 16 (Render managed)
                    │
                    ├── SQLite (本地开发)
                    ├── Swagger UI (/docs)
                    ├── Jinja2 模板 (Bootstrap 5)
                    └── Ask AI (mock) → 未来调用 LLM API 微服务
```

**技术栈:**

| 层 | 技术 |
|---|------|
| 框架 | FastAPI 0.115 |
| ORM | SQLAlchemy 2.0 |
| 迁移 | Alembic |
| 认证 | JWT (python-jose) + bcrypt |
| 数据库 | PostgreSQL 16 (prod) / SQLite (dev) |
| 前端 | Bootstrap 5 + Chart.js + Jinja2 |
| 测试 | pytest + httpx（28 测试，全绿） |
| 容器 | Docker + docker-compose |
| 部署 | Render（自动 Docker 构建 + 健康检查） |

**统计数据:**

| 指标 | 数值 |
|------|------|
| API 端点 | 16 |
| 数据库表 | 3 (products, categories, users) |
| FK 关系 | 1 (Product → Category) |
| 测试 | 28（全部通过） |
| Docker 服务 | 2 (app + db) |

---

## 待改进 (What Still Needs Work)

### 🔴 关键问题

| # | 问题 | 当前状态 | 建议方向 |
|---|------|---------|---------|
| 1 | **Ask AI 太弱** | 关键词匹配 mock，问 "qty" 和 "quantity" 行为不一致，不理解同义词 | Phase 2 接入真实 LLM API（OpenAI/Claude），自然语言 → SQL 生成 |
| 2 | **前端无 auth UI** | API 有 JWT，但前端页面没有登录/注册界面，add/edit 不验证 | 添加登录页面，前端 add/edit 按钮在未登录时隐藏或要求登录 |
| 3 | **Categories 页面隐藏太深** | 用户可能不知道 Navbar 里有 Categories 链接 | 在 Add Item 页面的分类下拉旁边加 "Manage Categories" 链接 |
| 4 | **无数据持久化保证** | Render 免费 PostgreSQL 90 天过期；SQLite 数据每次部署丢失 | 迁移到付费 PostgreSQL 或添加数据导出功能 |

### 🟡 体验优化

| # | 问题 | 建议 |
|---|------|------|
| 5 | 搜索框不区分大小写，但不支持模糊/拼音 | 保持现状，LLM 接入后自然解决 |
| 6 | 图表只显示前 10，无筛选功能 | 添加按分类筛选图表 |
| 7 | Edit/Delete 操作无 CSRF 保护 | 如果是内部工具可接受；公开部署需加 CSRF token |
| 8 | 手机端响应式勉强可用 | 表格在小屏幕上水平滚动不够好 |

### 🟢 未来功能（Phase 2-3）

| # | 功能 | 说明 |
|---|------|------|
| 9 | **LLM API 微服务** | 独立容器，真实 GPT/Claude 调用。Inventory System 通过 `/api/ask` 调用 LLM 服务 |
| 10 | **微服务联动** | `/api/ask` 从 mock 改为调用 LLM API 容器，展示系统设计能力 |
| 11 | **数据导入/导出** | CSV 导入导出，方便演示数据 |
| 12 | **GitHub Actions CI** | 自动测试 + lint + Docker 构建验证 |
| 13 | **Cover Letter 生成** | 结合 career-ops 项目，CV + JD → LLM → 生成 cover letter |

---

## CV 上可以写的（简历弹药）

基于目前已实现的功能，可以在简历上诚实写这些：

**项目：Inventory Management System v2**
> 独立设计并开发了全栈库存管理系统后端，使用 FastAPI + SQLAlchemy + PostgreSQL，实现了：
> - RESTful API（16 个端点），含 Swagger 自动文档
> - JWT Bearer 认证（bcrypt 密码哈希 + access/refresh token）
> - 自然语言查询接口（/api/ask），通过关键词匹配将英文/中文问题映射为 SQL 查询
> - 关系型数据库设计（Category ← Product 外键约束，Alembic 迁移管理）
> - Docker 容器化部署（Render + docker-compose，PostgreSQL 生产环境，SQLite 本地开发）
> - 28 个 pytest 自动化测试，覆盖 CRUD、认证、Ask AI
> - Bootstrap 5 前端（Jinja2 模板、Chart.js 可视化、行内表单编辑）
> - 分类管理（FK 约束保护删除）

---

## 项目演化时间线

| 日期 | 里程碑 |
|------|--------|
| Phase 0 | FastAPI 脚手架（config, database, main） |
| Phase 1 | Models (Category, Product, User) + Alembic + Products CRUD + 9 tests |
| Phase 2 | JWT Auth (register/login/refresh) + 保护路由 + 9 tests |
| Phase 3 | /api/ask 端点 (mock LLM, 关键词 → SQL) + 10 tests |
| Phase 5 | Dockerfile + docker-compose + Render 部署 + README |
| Phase 6 | Bootstrap 前端（Dashboard, Add/Edit forms, Categories 管理） |
| 修复迭代 | Ask AI 重写（产品感知匹配）、Categories 行内编辑、表单错误行内提示 |
