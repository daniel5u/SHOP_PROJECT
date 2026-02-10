# Shop Project — RAG + Tool Calling 电商助手（Django + Qdrant）

一个“可落地”的电商后端项目：在常规 **商品/购物车/订单/JWT** 接口之上，集成 **RAG 检索** 与 **Agent Tool Calling**，并使用 **Qdrant 向量数据库**实现语义搜索；支持 **Embedding + Rerank** 的可插拔检索链路；同时提供 **Amazon 数据爬虫**用于构建商品知识库/评测集。

---

## 核心亮点

- **RAG / 语义检索**：将商品信息向量化写入 Qdrant，在 `/api/search/` 进行语义检索与结构化过滤。
- **Tool Calling（Agent）**：基于 **LangGraph + LangChain Tools**，LLM 以 JSON Schema 方式发起工具调用，后端做安全分发与结果回填。
- **Qdrant 向量数据库**：
  - 商品语义检索 collection：`products`（用于商品搜索）
  - 知识库 RAG collection：`product_knowledge`（用于文档型检索/知识注入）
- **Rerank（可选）**：内置 CrossEncoder Rerank（`BAAI/bge-reranker-base`），用于“先召回、再精排”的搜索增强（当前在 `products/services.py` 里提供了可启用版本）。
- **数据爬虫**：Playwright 并发抓取 Amazon 商品信息/评论摘要，产出 CSV 作为知识库数据源（见 `scrap_amazon/`）。
- **可观测性**：关键检索逻辑用 `langsmith.traceable` 标注（便于 trace / 评测对比）。

---

## 架构与链路

### 1) 语义搜索（Qdrant）

请求入口：`/api/search/`（详见 `shop_backend/API_Documentation.md`）

- **向量化**：`shop_backend/utils/embedding.py`（`Qwen/Qwen3-Embedding-0.6B`）
- **检索**：`shop_backend/utils/qdrant_search.py`
  - 支持 brand/category/title/price/rating 的 payload filter
  - 默认返回 top-k（并携带 score）
- **后端业务编排**：`shop_backend/products/services.py` → `smart_search()`
  - `asin` 精确匹配 → MySQL
  - 否则 → Qdrant 语义检索
  - 异常兜底 → MySQL 模糊匹配

### 2) Agent Tool Calling（LangGraph）

请求入口：`/api/chat/`（见 `shop_backend/agent/views.py`）

- **LLM**：`deepseek-chat`（`shop_backend/agent/agent.py`，通过 `DEEPSEEK_API_KEY` 配置）
- **工具定义**：`shop_backend/agent/tools.py`
  - `smart_search_tool`（语义检索）
  - `add_to_cart_tool` / `list_cart_tool` / `clear_cart_tool`
  - `search_user_order_tool`
  - `search_reviews_tool`
  - `change_user_info_tool`
  - `memorize_user_info_tool`（长期记忆写入）
- **工具分发器（关键）**：`shop_backend/agent/agent.py` → `dispatch_tool()`
  - 解决“工具调用如何绑定当前用户”的问题
  - 对需要登录的工具做登录态约束

### 3) Memory（短期摘要 + 长期画像）

`shop_backend/agent/memory.py`

- **短期记忆**：Redis 存对话历史（按 session）
- **自动摘要**：超过阈值后将历史压缩为 summary，保留最近若干轮
- **长期记忆**：Redis Hash 存用户画像（偏好/预算/地址等），注入 System Prompt

---

## 目录结构（重点模块）

```text
shop_backend/                 # Django/DRF 后端
  agent/                      # Agent（LangGraph + Tools + Memory）
    agent.py                  # 核心图编排、tool dispatcher、LLM 绑定 tools
    tools.py                  # @tool 工具定义（Tool Call Schema）
    memory.py                 # Redis 记忆（摘要 + 用户画像）
    rag/                      # 简化版 RAG（knowledge collection）
  products/                   # 商品模块（含 smart_search 入口）
  utils/
    embedding.py              # Embedding（Qwen3-Embedding-0.6B）
    qdrant_search.py          # Qdrant 检索封装（payload filter）
    reranker.py               # Rerank（BAAI/bge-reranker-base）
scrap_amazon/                 # Playwright Amazon 爬虫（构建知识库 CSV）
shop_frontend/                # React + Vite 前端（可选）
```

---

## 快速开始（本地开发）

### 依赖概览

- **Python**：Django / DRF / LangChain / LangGraph / Qdrant client / SentenceTransformers / Redis client
- **MySQL**：业务数据（商品/订单/用户）
- **Qdrant**：向量库（语义检索 / RAG）
- **Redis**：对话记忆（短期摘要 + 长期画像）

### 1) 配置环境变量

在 `shop_backend/` 下创建 `.env`：

```bash
DEEPSEEK_API_KEY=your_api_key
REDIS_URL=redis://localhost:6379/0
```

### 2) 启动 MySQL / Qdrant / Redis

- **MySQL**：按 `shop_backend/backend/settings.py` 的数据库配置准备库与账号
- **Qdrant**：默认 `localhost:6333`
- **Redis**：默认 `localhost:6379`

### 3) 启动后端

在 `shop_backend/` 目录：

```bash
python manage.py migrate
python manage.py runserver
```

接口基址默认是：`http://localhost:8000/api`（详见 `shop_backend/API_Documentation.md`）

---

## 向量库初始化与数据同步

### 1) 将 MySQL 商品同步到 Qdrant（collection: `products`）

管理命令：`shop_backend/products/management/commands/sync_product_to_qdrant.py`

在 `shop_backend/` 目录执行：

```bash
python manage.py sync_product_to_qdrant
```

会做的事：

- 拼装商品富文本（title/brand/spec/category/description）
- 使用 `QwenEmbeddingService` 生成向量
- 写入 Qdrant collection `products`，payload 含 `asin/title/brand/category/price/rating`

---

## Rerank（精排）说明

`shop_backend/utils/reranker.py` 使用 CrossEncoder：`BAAI/bge-reranker-base`。

- **适用场景**：召回 top50（向量相似度）后，用 rerank_score 重新排序，提高 topK 命中率
- **项目现状**：在 `shop_backend/products/services.py` 中提供了“Qdrant + rerank”的实现草案（注释块），可一键切换策略做 AB 对比与评估。

---

## 爬虫与知识库数据（Amazon）

`scrap_amazon/final_amazon_scraper.py`（Playwright）

- **输入**：`scrap_amazon/amazon_links.csv`（商品 URL/ASIN）
- **输出**：`scrap_amazon/rag_knowledge_base.csv`
- **抓取字段**：title/price/image_url/brand/category/specifications/rating/description/reviews_text 等
- **工程化点**：
  - 并发控制（`MAX_CONCURRENT_TASKS`）
  - 代理/VPN 支持
  - cookies 注入与反爬伪装（降低 CAPTCHA）
  - 断点续传（已抓取的 url 会跳过）

---

## API 文档

- 后端 API：`shop_backend/API_Documentation.md`

---
