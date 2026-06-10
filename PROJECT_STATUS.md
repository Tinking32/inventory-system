# Inventory System v2 — Project Status

> Last updated: 2026-06-11
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
| Ask AI | `/api/ask/` | POST | 自然语言查询（产品感知关键词匹配） |
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
| Add Item | `/add` | 添加产品表单（分类自动检测 + Manage 链接 + 负数校验） |
| Edit Item | `/edit/{id}` | 编辑产品表单（负数校验） |
| Import | `/import` | CSV 批量导入：上传 → 预览验证 → 执行导入 + 自动分类 |
| Categories | `/categories` | 分类管理：添加、✏️行内重命名、🗑️删除（FK 保护） |

### Ask AI 能力 (Natural Language Query)

| 问题类型 | 示例 | 回复 |
|---------|------|------|
| 产品数量查询 | "how many Dell Monitors do we have?" | "Dell Monitor has 5 units in stock (threshold: 10)" |
| 产品价格查询 | "what is the price of Logitech Mouse?" | "Logitech Mouse costs $29.99 per unit" |
| 产品低库存查询 | "is Coca Cola low on stock?" | "No, Coca Cola has 150 units (threshold: 30)" |
| 产品详情 | "tell me about Logitech Mouse" | 📦 完整产品信息卡片 |
| 低库存汇总 | "which products are low on stock?" | 列出所有低于阈值的商品 |
| 最贵商品 | "what is the most expensive product?" | 返回价格最高的商品 |
| 最便宜商品 | "cheapest product" | 返回价格最低的商品 |
| 库存总值 | "total value of inventory" | "$X,XXX.XX across Y products" |
| 分类筛选 | "list products in Electronics" | 返回该分类下所有商品 |
| 中文支持 | "哪些货库存不足？" | 同上 low_stock 查询 |

### CSV 导入 (Data Import)

| 步骤 | 功能 |
|------|------|
| 上传 | 选择 .csv 文件，页面显示格式说明和下载示例 |
| 预览 | 解析每行数据，显示 ✅/❌ 状态，错误信息行内展示 |
| 自动分类 | category 列为空时，根据产品名称关键词自动匹配分类（"Mouse" → Electronics） |
| 验证 | 重复名称检测、非法数值检测、未知分类检测、必填字段检测 |
| 执行 | 一键导入所有有效行，新分类自动创建 |

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
│   │   ├── frontend.py      # 前端路由（/, /add, /edit, /import, /categories）
│   │   ├── products.py      # 产品 CRUD API（POST/PUT/DELETE 需 JWT）
│   │   ├── categories.py    # 分类 API
│   │   ├── auth.py          # 注册/登录/刷新/me
│   │   └── ask.py           # POST /api/ask
│   ├── services/
│   │   ├── auth.py          # bcrypt 密码哈希 + JWT 令牌
│   │   ├── ask_service.py   # 产品感知关键词匹配 → SQL（mock LLM 模式）
│   │   ├── category_auto.py # 产品名称 → 分类自动匹配
│   │   └── csv_import.py    # CSV 解析、验证、导入执行
│   └── templates/           # Jinja2 模板（Bootstrap 5 + Chart.js）
├── examples/
│   └── sample_import.csv    # CSV 导入示例文件（12 条真实数据）
├── seed.py                  # 数据库种子脚本（14 条真实数据）
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
                    ├── Jinja2 模板 (Bootstrap 5 + Chart.js)
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
| 服务模块 | 4 (auth, ask_service, category_auto, csv_import) |
| 模板页面 | 5 (index, add, edit, categories, import) |
| 测试 | 28（全部通过） |
| Docker 服务 | 2 (app + db) |
| 种子数据 | 14 产品 × 4 分类 |

---

## 已修复的 UX 问题 (Fixed)

| # | 问题 | 解决方案 |
|---|------|---------|
| 1 | Categories 行内编辑文字和输入框同时显示 | Bootstrap `d-none` 严格切换 + borderless 输入框 |
| 2 | Add Item 表单分类下拉与下方标签重叠 | `mb-4` 间距 + `position:relative; z-index:10` |
| 3 | Chart.js 单条数据变成巨大蓝墙 | `maxBarThickness: 80` 限制柱宽 |
| 4 | Search/Reset 按钮间距松散 | `input-group` 粘合输入框和按钮 |
| 5 | Ask AI 显示调试信息 | 移除 `Query type | Results | Mode` 行 |
| 6 | 产品无分类（全是 None） | 重新种子 + 自动分类检测 |
| 7 | 负数 qty/price 无保护 | 前端 `min="0"` + 后端校验 "must be >= 0" |

---

## 待改进 (Still Needs Work)

### 🔴 关键

| # | 问题 | 建议 |
|---|------|------|
| 1 | **Ask AI 关键词匹配局限性** | 接入真实 LLM API（OpenAI/Claude），自然语言 → SQL 生成 |
| 2 | **前端无 auth UI** | 登录页面 + 未登录时隐藏 Add/Edit/Delete 按钮 |
| 3 | **CSV 导入使用隐藏 textarea 传数据** | 大量数据时 URL/表单体积过大。改用服务端 session 或分片上传 |
| 4 | **无数据持久化保证** | Render 免费 PostgreSQL 90 天过期 |

### 🟡 体验优化

| # | 问题 | 建议 |
|---|------|------|
| 5 | Edit/Delete 无 CSRF 保护 | 公开部署需加 CSRF token |
| 6 | 手机端响应式一般 | 表格在小屏幕上需水平滚动 |
| 7 | 无数据导出功能 | CSV 导出（对称于导入功能） |

### 🟢 未来功能

| # | 功能 | 说明 |
|---|------|------|
| 8 | **LLM API 微服务** | 独立 Docker 容器，真实 GPT/Claude 调用 |
| 9 | **微服务联动** | /api/ask 从 mock 改为调用 LLM API 容器 |
| 10 | **GitHub Actions CI** | 自动测试 + Docker 构建验证 |
| 11 | **多仓库 (Multi-Warehouse)** | Warehouse 表 + ProductWarehouse 中间表（多对多） |
| 12 | **上架/下架状态** | Product.active 字段，库存为 0 自动下架 |

---

## 简历弹药 (Resume Bullets)

> **Inventory Management System v2** — 独立设计开发的全栈库存管理系统
> - FastAPI + SQLAlchemy + PostgreSQL，16 个 REST API 端点，Swagger 自动文档
> - JWT Bearer 认证（bcrypt 哈希 + access/refresh token）
> - 自然语言查询接口，产品感知关键词匹配将英文/中文问题映射为 SQL 查询
> - CSV 批量导入：上传 → 行级验证 → 自动分类检测 → 一键执行
> - 分类自动检测引擎：基于产品名称关键词的规则匹配
> - 关系型数据库设计（Category ← Product FK，Alembic 迁移管理）
> - Docker 容器化部署（Render + docker-compose，PostgreSQL 生产，SQLite 开发）
> - 28 个 pytest 自动化测试（CRUD + Auth + Ask AI）
> - Bootstrap 5 前端（Chart.js 可视化、行内编辑、CSV 导入向导）

---

## 项目演化时间线

| 日期 | 里程碑 |
|------|--------|
| Phase 0 | FastAPI 脚手架（config, database, main） |
| Phase 1 | Models (Category, Product, User) + Alembic + Products CRUD |
| Phase 2 | JWT Auth + 保护路由 |
| Phase 3 | /api/ask 端点 (mock LLM) |
| Phase 5 | Docker + Render 部署 |
| Phase 6 | Bootstrap 前端（Dashboard, Add/Edit, Categories） |
| 2026-06-10 | Ask AI 重写（产品感知匹配）、Categories 行内编辑、表单负数校验 |
| 2026-06-11 | CSV 导入（上传→预览→执行）、分类自动检测、Chart.js 优化、种子数据、Search bar 收紧 |
