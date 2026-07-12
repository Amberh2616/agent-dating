# Technical Design Document (TDD)
## Agent-Dating: AI 代理社交平台

**版本**: 1.0
**日期**: 2026-01-29
**作者**: Claude Code AI

---

## 目錄

1. [簡介](#1-簡介)
2. [技術選型](#2-技術選型)
3. [系統架構](#3-系統架構)
4. [部署架構](#4-部署架構)
5. [第三方服務整合](#5-第三方服務整合)
6. [背景任務系統](#6-背景任務系統)
7. [效能設計](#7-效能設計)
8. [可擴展性設計](#8-可擴展性設計)
9. [監控與日誌](#9-監控與日誌)
10. [災難復原](#10-災難復原)
11. [開發環境設置](#11-開發環境設置)
12. [測試策略](#12-測試策略)

---

## 1. 簡介

### 1.1 文件目的

本文件為 Agent-Dating 專案的技術設計文件 (Technical Design Document)，詳述技術選型理由、部署架構、效能考量及開發實踐，供技術團隊參考實施。

### 1.2 目標讀者

- 後端開發工程師
- 前端開發工程師
- DevOps 工程師
- 技術主管

### 1.3 專案概述

Agent-Dating 是基於 **生成式代理 (Generative Agents)** 架構的 AI 社交平台，採用 Django + Phaser 3 技術棧，整合 Groq LLM 提供智能對話能力。

---

## 2. 技術選型

### 2.1 技術棧總覽

```
┌─────────────────────────────────────────────────────────────┐
│                      Technology Stack                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Frontend                                                     │
│  ├── Phaser 3.80.1 (遊戲引擎)                                │
│  ├── Vanilla JavaScript (ES6+)                               │
│  ├── CSS3 (動畫、佈局)                                        │
│  └── Habbo Avatar API (角色渲染)                             │
│                                                               │
│  Backend                                                      │
│  ├── Python 3.11+                                            │
│  ├── Django 5.0                                              │
│  ├── Django REST Framework 3.14                              │
│  ├── Django Channels 4.0 (WebSocket)                         │
│  └── Celery 5.3 (背景任務)                                   │
│                                                               │
│  AI Layer                                                     │
│  ├── LangChain 0.1.x                                         │
│  ├── Groq API (llama-3.3-70b-versatile)                      │
│  └── 自研 Memory/Reflection/Intent 系統                      │
│                                                               │
│  Infrastructure                                               │
│  ├── PostgreSQL 15 (生產)                                    │
│  ├── SQLite 3 (開發)                                         │
│  ├── Redis 7 (快取 + 消息佇列)                               │
│  └── Docker + Docker Compose                                 │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 後端技術選型理由

#### 2.2.1 Django 5.0

| 考量因素 | Django | FastAPI | Flask |
|---------|--------|---------|-------|
| **ORM** | 內建強大 | 需 SQLAlchemy | 需 SQLAlchemy |
| **Admin** | 內建 | 無 | 無 |
| **生態系統** | 最成熟 | 新興 | 成熟 |
| **WebSocket** | Channels 整合 | 原生支援 | 需 Flask-SocketIO |
| **學習曲線** | 中等 | 低 | 低 |
| **適合場景** | 複雜業務系統 | API 服務 | 小型專案 |

**選擇理由**:
- Django ORM 對複雜資料模型（靈魂檔案、記憶系統）支援良好
- Django Admin 方便管理後台數據
- Django Channels 與 Celery 整合成熟

#### 2.2.2 Django Channels 4.0

**為什麼選擇 Channels 而非 Socket.IO:**
- 與 Django 生態系統原生整合
- 支援同步和非同步 Consumer
- Channel Layer 可使用 Redis 實現水平擴展

#### 2.2.3 Celery 5.3

**為什麼選擇 Celery:**
- Python 生態系統中最成熟的分散式任務佇列
- 支援定時任務 (Celery Beat 或 APScheduler)
- 與 Django 整合簡單
- 支援任務重試、優先級、結果後端

### 2.3 前端技術選型理由

#### 2.3.1 Phaser 3 vs 其他方案

| 考量因素 | Phaser 3 | PixiJS | Unity WebGL |
|---------|----------|--------|-------------|
| **學習曲線** | 中等 | 較陡 | 陡峭 |
| **等距地圖** | 原生支援 | 需自行實現 | 完整支援 |
| **檔案大小** | ~1MB | ~500KB | >10MB |
| **文檔品質** | 優秀 | 良好 | 優秀 |
| **Habbo 整合** | 簡單 | 簡單 | 複雜 |

**選擇理由**:
- Phaser 3.50+ 內建等距地圖支援
- 輕量級，載入速度快
- 社群活躍，範例豐富

#### 2.3.2 為什麼不使用 Vue/React

**決策理由**:
- 專案核心是 Phaser 3 遊戲場景，非傳統 Web App
- 減少框架依賴和建置複雜度
- 聊天 UI 相對簡單，原生 JavaScript 足夠

### 2.4 AI 技術選型理由

#### 2.4.1 Groq vs OpenAI vs 本地 LLM

| 考量因素 | Groq | OpenAI | 本地 LLM |
|---------|------|--------|----------|
| **成本** | 免費額度大 | 按量計費 | 硬體成本 |
| **速度** | 極快 (~100 tokens/s) | 快 (~50 tokens/s) | 依硬體 |
| **品質** | 優秀 (70B) | 最佳 (GPT-4) | 依模型 |
| **延遲** | 低 | 中 | 低 |
| **Embedding** | 不支援 | 支援 | 支援 |

**選擇理由**:
- 開發階段使用免費 Groq，節省成本
- llama-3.3-70b-versatile 品質接近 GPT-4
- 推理速度極快，適合即時對話

#### 2.4.2 LangChain 整合

**為什麼使用 LangChain**:
- 統一的 LLM 介面，方便切換 Provider
- 內建 Message 類型 (System/Human/AI)
- 支援 async/await

**LangChain 使用範圍**:
- ✅ LLM 調用封裝
- ✅ Message 格式轉換
- ❌ Agent/Chain (過度複雜，自行實現)
- ❌ Memory (自行實現更靈活)

### 2.5 資料庫選型

#### 2.5.1 PostgreSQL 15

**為什麼選擇 PostgreSQL**:
- JSONB 支援複雜 JSON 結構 (靈魂檔案、情緒狀態)
- 優秀的並發處理能力
- pgvector 擴展支援向量搜尋 (未來)

#### 2.5.2 開發使用 SQLite

**理由**:
- 零設定，快速啟動
- 適合本地開發和測試
- Django ORM 抽象層保證遷移無縫

### 2.6 版本需求

| 元件 | 最低版本 | 建議版本 |
|------|---------|---------|
| Python | 3.10 | 3.11+ |
| Node.js | 18 | 20+ |
| PostgreSQL | 14 | 15 |
| Redis | 6 | 7 |
| Docker | 20.10 | 24+ |

---

## 3. 系統架構

### 3.1 高階架構圖

```
┌────────────────────────────────────────────────────────────────────┐
│                           INTERNET                                  │
└──────────────────────────────┬─────────────────────────────────────┘
                               │
                               ▼
┌────────────────────────────────────────────────────────────────────┐
│                        LOAD BALANCER                                │
│                     (Nginx / Cloud LB)                              │
└──────────────────────────────┬─────────────────────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   Web Server    │  │  WebSocket      │  │   Static        │
│   (Gunicorn)    │  │  (Daphne)       │  │   (CDN/Nginx)   │
│   Port: 8000    │  │  Port: 8001     │  │   Port: 80/443  │
└────────┬────────┘  └────────┬────────┘  └─────────────────┘
         │                    │
         └────────┬───────────┘
                  │
                  ▼
┌────────────────────────────────────────────────────────────────────┐
│                      DJANGO APPLICATION                             │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    Django Middleware                          │  │
│  │  (Auth, CORS, Logging, Exception Handling)                    │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                │                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                │
│  │   REST API  │  │  WebSocket  │  │   Celery    │                │
│  │  (DRF)      │  │  Consumers  │  │   Tasks     │                │
│  └─────────────┘  └─────────────┘  └─────────────┘                │
│                                │                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    AI Service Layer                           │  │
│  │  (LLMService, SoulAgent, SocialAgent)                         │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   PostgreSQL    │  │     Redis       │  │   Groq API      │
│   (Data Store)  │  │ (Cache+Queue)   │  │   (LLM)         │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

### 3.2 請求流程

#### 3.2.1 REST API 請求流程

```
Client Request
      │
      ▼
┌─────────────────┐
│  Load Balancer  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Gunicorn     │──→ 多進程處理
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Django Middleware│
│ ├─ JWTAuth      │
│ ├─ CORS         │
│ └─ Logging      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   URL Router    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    DRF View     │
│ ├─ Serializer   │
│ └─ QuerySet     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Django ORM    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   PostgreSQL    │
└─────────────────┘
```

#### 3.2.2 WebSocket 連接流程

```
Client WebSocket
      │
      ▼
┌─────────────────┐
│    Daphne       │──→ ASGI Server
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Channels Router │
│ ├─ /ws/chat/    │──→ ChatConsumer
│ └─ /ws/world/   │──→ WorldConsumer
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ TokenAuthMiddle │
│   ware          │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Consumer     │
│ ├─ connect()    │
│ ├─ receive()    │
│ └─ disconnect() │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Channel Layer  │
│  (Redis)        │
└─────────────────┘
```

### 3.3 資料流

#### 3.3.1 AI 對話資料流

```
User sends message
         │
         ▼
┌─────────────────────────────────────────────┐
│  POST /api/chat/conversations/{id}/send/     │
│  ├─ Validate input                           │
│  ├─ Save Message (sender_type='user')        │
│  └─ Trigger Celery task (async)              │
└────────────────────┬────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────┐
│  Celery: generate_agent_response             │
│  ├─ Check conversation.mode                  │
│  ├─ Load Agent + SoulProfile                 │
│  ├─ Retrieve memories (10 related)           │
│  ├─ Get emotion description                  │
│  ├─ Get recent reflections (5)               │
│  └─ Build system prompt                      │
└────────────────────┬────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────┐
│  SoulAgent.generate_response()               │
│  ├─ Construct messages list                  │
│  └─ Call LLMService.generate_response()      │
└────────────────────┬────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────┐
│  Groq API                                    │
│  ├─ Model: llama-3.3-70b-versatile           │
│  ├─ Temperature: 0.9                         │
│  └─ Max tokens: 500                          │
└────────────────────┬────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────┐
│  Post-processing                             │
│  ├─ Save Message (sender_type='agent')       │
│  ├─ Update Agent.last_chat_message           │
│  ├─ Update Agent.emotion_state               │
│  ├─ Broadcast to ChatConsumer                │
│  └─ Broadcast chat bubble to WorldConsumer   │
└─────────────────────────────────────────────┘
```

---

## 4. 部署架構

### 4.1 開發環境架構

```
┌─────────────────────────────────────────────────────────────┐
│                    Development Environment                   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Terminal 1: Django                                           │
│  └─ python manage.py runserver (port 8000)                   │
│                                                               │
│  Terminal 2: Celery Worker                                    │
│  └─ celery -A config worker -l info                          │
│                                                               │
│  Terminal 3: Frontend                                         │
│  └─ npx serve frontend -p 3000                               │
│                                                               │
│  Background: Redis                                            │
│  └─ redis-server (port 6379)                                 │
│                                                               │
│  Database: SQLite                                             │
│  └─ db.sqlite3                                               │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 生產環境架構

```
┌─────────────────────────────────────────────────────────────────────┐
│                       Production Architecture                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│                           ┌─────────────────┐                        │
│                           │   CloudFlare    │                        │
│                           │   (CDN + DDoS)  │                        │
│                           └────────┬────────┘                        │
│                                    │                                  │
│                           ┌────────▼────────┐                        │
│                           │     Nginx       │                        │
│                           │ (Reverse Proxy) │                        │
│                           └────────┬────────┘                        │
│                                    │                                  │
│            ┌───────────────────────┼───────────────────────┐         │
│            │                       │                       │         │
│    ┌───────▼───────┐      ┌───────▼───────┐      ┌───────▼───────┐  │
│    │   Gunicorn    │      │    Daphne     │      │    Static     │  │
│    │   (x4 workers)│      │  (WebSocket)  │      │   (Nginx)     │  │
│    │   Port: 8000  │      │   Port: 8001  │      │   /static/    │  │
│    └───────────────┘      └───────────────┘      └───────────────┘  │
│            │                       │                                  │
│            └───────────┬───────────┘                                  │
│                        │                                              │
│    ┌───────────────────▼───────────────────┐                         │
│    │        Docker Compose Network          │                         │
│    │                                         │                         │
│    │  ┌─────────────┐  ┌─────────────────┐  │                         │
│    │  │   Django    │  │  Celery Worker  │  │                         │
│    │  │  Container  │  │   Container     │  │                         │
│    │  └─────────────┘  └─────────────────┘  │                         │
│    │                                         │                         │
│    │  ┌─────────────┐  ┌─────────────────┐  │                         │
│    │  │ PostgreSQL  │  │      Redis      │  │                         │
│    │  │  Container  │  │    Container    │  │                         │
│    │  └─────────────┘  └─────────────────┘  │                         │
│    │                                         │                         │
│    └─────────────────────────────────────────┘                         │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.3 Docker Compose 設定

```yaml
# docker-compose.yml
version: '3.8'

services:
  # Django Web Application
  web:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4
    volumes:
      - ./backend:/app
      - static_volume:/app/staticfiles
    expose:
      - 8000
    environment:
      - DEBUG=False
      - DATABASE_URL=postgres://user:pass@db:5432/agent_dating
      - REDIS_URL=redis://redis:6379/0
      - GROQ_API_KEY=${GROQ_API_KEY}
    depends_on:
      - db
      - redis

  # Daphne (WebSocket)
  websocket:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: daphne -b 0.0.0.0 -p 8001 config.asgi:application
    volumes:
      - ./backend:/app
    expose:
      - 8001
    environment:
      - DEBUG=False
      - DATABASE_URL=postgres://user:pass@db:5432/agent_dating
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

  # Celery Worker
  celery:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A config worker -l info --concurrency=4
    volumes:
      - ./backend:/app
    environment:
      - DEBUG=False
      - DATABASE_URL=postgres://user:pass@db:5432/agent_dating
      - REDIS_URL=redis://redis:6379/0
      - GROQ_API_KEY=${GROQ_API_KEY}
    depends_on:
      - db
      - redis

  # APScheduler (定時任務)
  scheduler:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: python manage.py runscheduler
    volumes:
      - ./backend:/app
    environment:
      - DEBUG=False
      - DATABASE_URL=postgres://user:pass@db:5432/agent_dating
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

  # PostgreSQL Database
  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=agent_dating

  # Redis (Cache + Message Queue)
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  # Nginx (Reverse Proxy)
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - static_volume:/var/www/static
      - ./frontend:/var/www/frontend
    depends_on:
      - web
      - websocket

volumes:
  postgres_data:
  redis_data:
  static_volume:
```

### 4.4 Nginx 設定

```nginx
# nginx.conf
upstream django {
    server web:8000;
}

upstream websocket {
    server websocket:8001;
}

server {
    listen 80;
    server_name your-domain.com;

    # Static files
    location /static/ {
        alias /var/www/static/;
    }

    # Frontend
    location / {
        root /var/www/frontend;
        try_files $uri $uri/ /index.html;
    }

    # REST API
    location /api/ {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # Admin
    location /admin/ {
        proxy_pass http://django;
        proxy_set_header Host $host;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://websocket;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }
}
```

---

## 5. 第三方服務整合

### 5.1 Groq API 整合

#### 5.1.1 服務概述

| 項目 | 說明 |
|------|------|
| **Provider** | Groq |
| **Model** | llama-3.3-70b-versatile |
| **用途** | 對話生成、反思生成、摘要生成 |
| **計費** | 免費額度 (開發)，按量計費 (生產) |

#### 5.1.2 整合架構

```python
# ai/llm.py

from langchain_groq import ChatGroq
from langchain.schema import SystemMessage, HumanMessage, AIMessage

class LLMService:
    """Singleton LLM 服務"""
    _instance = None
    _chat_model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _initialize_models(self):
        """惰性初始化 LLM 模型"""
        if self._chat_model is None:
            self._chat_model = ChatGroq(
                model=settings.GROQ_MODEL,  # llama-3.3-70b-versatile
                temperature=0.9,
                max_tokens=1000,
                api_key=settings.GROQ_API_KEY
            )

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.9,
        max_tokens: int = 1000
    ) -> str:
        """
        生成聊天回覆

        Args:
            messages: [{"role": "system|user|assistant", "content": "..."}]
            temperature: 創造性 (0-1)
            max_tokens: 最大輸出 token 數

        Returns:
            生成的文字回覆
        """
        self._initialize_models()

        # 轉換為 LangChain 訊息格式
        lc_messages = []
        for msg in messages:
            if msg['role'] == 'system':
                lc_messages.append(SystemMessage(content=msg['content']))
            elif msg['role'] == 'user':
                lc_messages.append(HumanMessage(content=msg['content']))
            elif msg['role'] == 'assistant':
                lc_messages.append(AIMessage(content=msg['content']))

        # 異步調用
        response = await self._chat_model.ainvoke(lc_messages)
        return response.content

# 全局實例
llm_service = LLMService()
```

#### 5.1.3 錯誤處理

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def generate_with_retry(self, messages, **kwargs):
    """帶重試的 LLM 調用"""
    try:
        return await self.generate_response(messages, **kwargs)
    except RateLimitError:
        logger.warning("Rate limit hit, waiting...")
        raise
    except APIConnectionError as e:
        logger.error(f"API connection error: {e}")
        raise
```

#### 5.1.4 成本控制

```python
# apps/agents/tasks.py

MAX_LLM_CALLS_PER_HOUR = 10      # 每小時最多調用次數
LLM_COOLDOWN_SECONDS = 30        # 調用冷卻時間
AI_CONVERSATION_MAX_ROUNDS = 3   # AI 對話最多輪數

def check_llm_limit(agent_id: str) -> bool:
    """檢查 LLM 調用限制"""
    cache_key = f"llm_calls_{agent_id}"
    calls = cache.get(cache_key, 0)
    if calls >= MAX_LLM_CALLS_PER_HOUR:
        return False
    cache.set(cache_key, calls + 1, 3600)  # 1 小時過期
    return True
```

### 5.2 Habbo Avatar API 整合

#### 5.2.1 服務概述

| 項目 | 說明 |
|------|------|
| **Provider** | Habbo (Sulake) |
| **URL** | https://www.habbo.com/habbo-imaging/avatarimage |
| **用途** | 生成像素風格角色圖片 |
| **計費** | 免費公開 API |

#### 5.2.2 Look Code 格式

```
hd-180-1.hr-828-61.ch-210-66.lg-270-64.sh-300-62

hd-{head_id}-{color}     頭型
hr-{hair_id}-{color}     髮型
ch-{chest_id}-{color}    上衣
lg-{legs_id}-{color}     下裝
sh-{shoes_id}-{color}    鞋子
```

#### 5.2.3 前端整合

```javascript
function getAvatarUrl(lookCode, direction = 2, headDirection = 2, action = 'std') {
    const params = new URLSearchParams({
        figure: lookCode,
        direction: direction,
        head_direction: headDirection,
        action: action,
        gesture: 'sml',  // 微笑
        size: 'l'        // 大尺寸
    });
    return `https://www.habbo.com/habbo-imaging/avatarimage?${params}`;
}

// 使用
const avatarImg = new Image();
avatarImg.src = getAvatarUrl(agent.avatar_look);
```

#### 5.2.4 錯誤處理

```javascript
function loadAvatar(lookCode, fallbackUrl) {
    return new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = () => resolve(img);
        img.onerror = () => {
            console.warn('Habbo API failed, using fallback');
            img.src = fallbackUrl;
            img.onload = () => resolve(img);
            img.onerror = reject;
        };
        img.src = getAvatarUrl(lookCode);
    });
}
```

### 5.3 Redis 整合

#### 5.3.1 用途

| 功能 | 說明 |
|------|------|
| **Celery Broker** | 任務消息佇列 |
| **Channel Layer** | WebSocket 群組通訊 |
| **Cache** | API 結果快取、LLM 調用限制 |
| **Session** | (可選) 會話存儲 |

#### 5.3.2 設定

```python
# config/settings.py

# Celery
CELERY_BROKER_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = CELERY_BROKER_URL

# Channels
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [os.environ.get('REDIS_URL', 'redis://localhost:6379/0')],
        },
    },
}

# Cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://localhost:6379/1'),
    }
}
```

---

## 6. 背景任務系統

### 6.1 架構概述

```
┌─────────────────────────────────────────────────────────────────┐
│                    Background Task System                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    Task Producers                         │    │
│  │  ├─ Django Views (API 觸發)                               │    │
│  │  ├─ WebSocket Consumers (即時事件觸發)                     │    │
│  │  └─ APScheduler (定時觸發)                                │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                    │
│                              ▼                                    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                     Redis Queue                           │    │
│  │  ├─ default: 一般任務                                     │    │
│  │  ├─ high: 高優先級 (AI 回覆)                              │    │
│  │  └─ low: 低優先級 (清理、統計)                            │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                    │
│                              ▼                                    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                   Celery Workers                          │    │
│  │  ├─ Worker 1: --concurrency=4                            │    │
│  │  ├─ Worker 2: --concurrency=4                            │    │
│  │  └─ Worker N: (可水平擴展)                                │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 Celery 設定

```python
# config/celery.py

from celery import Celery
from celery.schedules import crontab

app = Celery('agent_dating')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# 任務設定
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Taipei',
    enable_utc=True,

    # 任務路由
    task_routes={
        'apps.agents.tasks.generate_agent_response': {'queue': 'high'},
        'apps.agents.tasks.generate_conversation_summary': {'queue': 'default'},
        'apps.agents.tasks.cleanup_old_records': {'queue': 'low'},
    },

    # 重試設定
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)
```

### 6.3 APScheduler 定時任務

```python
# apps/agents/scheduler.py

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

scheduler = BackgroundScheduler()

# 定時任務配置
SCHEDULED_JOBS = [
    {
        'id': 'agent_simulation',
        'func': run_agent_simulation,
        'trigger': IntervalTrigger(seconds=10),
        'description': 'Agent 自主行動模擬'
    },
    {
        'id': 'reflection_generation',
        'func': check_and_generate_reflections,
        'trigger': IntervalTrigger(minutes=30),
        'description': '檢查並生成反思'
    },
    {
        'id': 'daily_goals',
        'func': generate_all_daily_goals,
        'trigger': CronTrigger(hour=0, minute=0),
        'description': '生成每日目標'
    },
    {
        'id': 'ai_conversation_trigger',
        'func': trigger_scheduled_ai_conversations,
        'trigger': IntervalTrigger(hours=1),
        'description': '觸發高配對分 AI 對話'
    },
    {
        'id': 'cleanup',
        'func': cleanup_old_records,
        'trigger': IntervalTrigger(hours=1),
        'description': '清理舊記錄'
    },
]

def start_scheduler():
    """啟動排程器"""
    for job in SCHEDULED_JOBS:
        scheduler.add_job(
            job['func'],
            trigger=job['trigger'],
            id=job['id'],
            replace_existing=True
        )
    scheduler.start()
```

### 6.4 任務清單

| 任務名稱 | 觸發方式 | 優先級 | 說明 |
|---------|---------|--------|------|
| `generate_agent_response` | API 觸發 | High | 生成 AI 回覆 |
| `run_ai_to_ai_conversation` | 決策觸發 | High | AI-to-AI 對話 |
| `generate_conversation_summary` | 對話後觸發 | Default | 生成對話摘要 |
| `generate_agent_reflections` | 每 5 次對話 | Default | 生成反思 |
| `apply_personality_growth` | 反思後觸發 | Low | 性格成長 |
| `run_agent_simulation` | 每 10 秒 | Default | Agent 模擬 |
| `cleanup_old_records` | 每小時 | Low | 清理舊記錄 |

### 6.5 任務重試策略

```python
@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300
)
def generate_agent_response(self, conversation_id: str):
    """
    生成 AI 回覆

    重試策略:
    - 最多重試 3 次
    - 初始延遲 60 秒
    - 指數退避，最大 300 秒
    """
    try:
        # 任務邏輯
        pass
    except RateLimitError as e:
        raise self.retry(exc=e, countdown=120)
    except Exception as e:
        logger.error(f"Task failed: {e}")
        raise
```

---

## 7. 效能設計

### 7.1 效能目標

| 指標 | 目標值 | 說明 |
|------|--------|------|
| **API 響應時間 (P95)** | < 200ms | 不含 AI 生成 |
| **AI 回覆延遲** | < 3s | 從發送到收到回覆 |
| **WebSocket 延遲** | < 50ms | 訊息廣播 |
| **並發用戶** | 1000+ | 同時在線 |
| **每秒請求 (RPS)** | 500+ | REST API |

### 7.2 資料庫優化

#### 7.2.1 索引策略

```python
# agents/models.py

class Memory(models.Model):
    # ...

    class Meta:
        indexes = [
            # 複合索引：Agent + 類型
            models.Index(fields=['agent', 'type']),
            # 複合索引：Agent + 重要性 (降序)
            models.Index(fields=['agent', '-importance']),
            # 複合索引：Agent + 時間 (降序)
            models.Index(fields=['agent', '-created_at']),
        ]

class MatchScore(models.Model):
    # ...

    class Meta:
        indexes = [
            models.Index(fields=['user_a', '-total_score']),
            models.Index(fields=['user_b', '-total_score']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['user_a', 'user_b'],
                name='unique_user_pair'
            )
        ]
```

#### 7.2.2 查詢優化

```python
# 使用 select_related 減少 N+1 查詢
conversations = Conversation.objects.select_related(
    'user_participant',
    'agent_participant',
    'other_agent'
).filter(is_active=True)

# 使用 prefetch_related 優化多對多
agents = Agent.objects.prefetch_related(
    'memories',
    'reflections'
).filter(is_online=True)

# 限制查詢數量
recent_memories = Memory.objects.filter(
    agent_id=agent_id
).order_by('-created_at')[:10]
```

### 7.3 快取策略

#### 7.3.1 快取層級

```
┌─────────────────────────────────────────────────────────────┐
│                      Cache Hierarchy                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  L1: Application Cache (In-Memory)                           │
│  ├─ LLM Service 實例 (Singleton)                            │
│  ├─ 常用配置 (settings)                                      │
│  └─ TTL: 應用生命週期                                        │
│                                                               │
│  L2: Redis Cache                                              │
│  ├─ API 結果快取                                             │
│  ├─ LLM 調用限制計數                                         │
│  ├─ 配對分數快取                                             │
│  └─ TTL: 1-60 分鐘                                           │
│                                                               │
│  L3: Database                                                 │
│  └─ 持久化數據                                               │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

#### 7.3.2 快取實現

```python
from django.core.cache import cache

def get_match_recommendations(user_id: str) -> list:
    """獲取配對推薦（帶快取）"""
    cache_key = f"match_recommendations_{user_id}"

    # 嘗試從快取讀取
    cached = cache.get(cache_key)
    if cached:
        return cached

    # 計算配對
    recommendations = calculate_recommendations(user_id)

    # 寫入快取 (30 分鐘)
    cache.set(cache_key, recommendations, 1800)

    return recommendations

def invalidate_match_cache(user_id: str):
    """用戶更新靈魂檔案時失效快取"""
    cache.delete(f"match_recommendations_{user_id}")
```

### 7.4 LLM 成本控制

```python
# 成本控制配置
LLM_RATE_LIMITS = {
    'max_calls_per_hour': 10,       # 每小時最多調用
    'cooldown_seconds': 30,          # 調用間隔
    'max_tokens_per_call': 500,      # 每次最大 token
    'ai_conversation_rounds': 3,     # AI 對話輪數
}

def should_allow_llm_call(agent_id: str) -> bool:
    """檢查是否允許 LLM 調用"""
    cache_key = f"llm_calls_{agent_id}"
    calls = cache.get(cache_key, 0)

    if calls >= LLM_RATE_LIMITS['max_calls_per_hour']:
        return False

    last_call_key = f"llm_last_call_{agent_id}"
    last_call = cache.get(last_call_key)

    if last_call:
        elapsed = time.time() - last_call
        if elapsed < LLM_RATE_LIMITS['cooldown_seconds']:
            return False

    # 更新計數
    cache.set(cache_key, calls + 1, 3600)
    cache.set(last_call_key, time.time(), 3600)

    return True
```

### 7.5 WebSocket 優化

```python
# 批量廣播
async def broadcast_room_updates(room_id: str, updates: list):
    """批量廣播房間更新"""
    channel_layer = get_channel_layer()

    # 合併更新為單一訊息
    message = {
        'type': 'room_batch_update',
        'updates': updates
    }

    await channel_layer.group_send(
        f'world_room_{room_id}',
        message
    )

# 心跳優化
HEARTBEAT_INTERVAL = 30  # 秒
HEARTBEAT_TIMEOUT = 90   # 秒

async def handle_heartbeat(self):
    """處理心跳"""
    if not hasattr(self, 'last_heartbeat'):
        self.last_heartbeat = time.time()

    if time.time() - self.last_heartbeat > HEARTBEAT_TIMEOUT:
        await self.close()
        return

    self.last_heartbeat = time.time()
    await self.send_json({'type': 'pong'})
```

---

## 8. 可擴展性設計

### 8.1 水平擴展策略

```
┌─────────────────────────────────────────────────────────────────┐
│                    Horizontal Scaling                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Web Tier (Stateless)                                            │
│  ├─ Gunicorn Worker 1 ──┐                                        │
│  ├─ Gunicorn Worker 2 ──┼─→ Load Balancer                        │
│  ├─ Gunicorn Worker 3 ──┤                                        │
│  └─ Gunicorn Worker N ──┘                                        │
│                                                                   │
│  WebSocket Tier                                                   │
│  ├─ Daphne Instance 1 ──┐                                        │
│  ├─ Daphne Instance 2 ──┼─→ Sticky Session (必要)                │
│  └─ Daphne Instance N ──┘                                        │
│       └─→ 透過 Redis Channel Layer 共享狀態                       │
│                                                                   │
│  Worker Tier                                                      │
│  ├─ Celery Worker 1 (concurrency=4) ──┐                          │
│  ├─ Celery Worker 2 (concurrency=4) ──┼─→ Redis Queue            │
│  └─ Celery Worker N ──────────────────┘                          │
│                                                                   │
│  Database Tier                                                    │
│  ├─ PostgreSQL Primary                                           │
│  ├─ PostgreSQL Read Replica 1                                    │
│  └─ PostgreSQL Read Replica N                                    │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 8.2 模組化設計

```
# 新增功能模組範例

# 1. 創建新 App
python manage.py startapp premium

# 2. 定義 Models
# apps/premium/models.py
class Subscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    plan = models.CharField(max_length=20)
    expires_at = models.DateTimeField()

# 3. 註冊 App
# config/settings.py
INSTALLED_APPS += ['apps.premium']

# 4. 創建 API
# apps/premium/views.py
class SubscriptionViewSet(viewsets.ModelViewSet):
    pass

# 5. 配置路由
# apps/premium/urls.py
router.register('subscription', SubscriptionViewSet)
```

### 8.3 LLM Provider 切換

```python
# ai/llm.py

from abc import ABC, abstractmethod

class BaseLLMProvider(ABC):
    @abstractmethod
    async def generate(self, messages: list, **kwargs) -> str:
        pass

class GroqProvider(BaseLLMProvider):
    async def generate(self, messages: list, **kwargs) -> str:
        # Groq 實現
        pass

class OpenAIProvider(BaseLLMProvider):
    async def generate(self, messages: list, **kwargs) -> str:
        # OpenAI 實現
        pass

class LLMFactory:
    _providers = {
        'groq': GroqProvider,
        'openai': OpenAIProvider,
    }

    @classmethod
    def get_provider(cls, name: str) -> BaseLLMProvider:
        provider_class = cls._providers.get(name)
        if not provider_class:
            raise ValueError(f"Unknown provider: {name}")
        return provider_class()
```

---

## 9. 監控與日誌

### 9.1 日誌配置

```python
# config/settings.py

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(levelname)s %(name)s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/app.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'json',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'ai': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

### 9.2 關鍵指標監控

| 指標類型 | 指標名稱 | 說明 |
|---------|---------|------|
| **API** | request_latency | 請求延遲 (ms) |
| **API** | request_count | 請求數量 |
| **API** | error_rate | 錯誤率 |
| **LLM** | llm_latency | LLM 調用延遲 |
| **LLM** | llm_token_usage | Token 使用量 |
| **WebSocket** | ws_connections | 活躍連接數 |
| **Celery** | task_success_rate | 任務成功率 |
| **Celery** | task_queue_length | 佇列長度 |
| **Database** | query_latency | 查詢延遲 |
| **Cache** | cache_hit_rate | 快取命中率 |

### 9.3 健康檢查端點

```python
# apps/health/views.py

from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['GET'])
def health_check(request):
    """健康檢查端點"""
    checks = {
        'database': check_database(),
        'redis': check_redis(),
        'celery': check_celery(),
    }

    all_healthy = all(checks.values())
    status_code = 200 if all_healthy else 503

    return Response({
        'status': 'healthy' if all_healthy else 'unhealthy',
        'checks': checks,
        'timestamp': timezone.now().isoformat()
    }, status=status_code)

def check_database():
    try:
        from django.db import connection
        connection.ensure_connection()
        return True
    except Exception:
        return False

def check_redis():
    try:
        from django.core.cache import cache
        cache.set('health_check', 'ok', 10)
        return cache.get('health_check') == 'ok'
    except Exception:
        return False

def check_celery():
    try:
        from config.celery import app
        app.control.ping(timeout=2)
        return True
    except Exception:
        return False
```

---

## 10. 災難復原

### 10.1 備份策略

| 備份類型 | 頻率 | 保留期限 | 說明 |
|---------|------|---------|------|
| **完整備份** | 每日 | 30 天 | 資料庫完整備份 |
| **增量備份** | 每小時 | 7 天 | WAL 日誌備份 |
| **Redis 快照** | 每 6 小時 | 3 天 | RDB 快照 |

### 10.2 備份腳本

```bash
#!/bin/bash
# backup.sh

# PostgreSQL 完整備份
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME \
    -F c -f /backups/db_$(date +%Y%m%d).dump

# Redis 快照
redis-cli -h $REDIS_HOST BGSAVE

# 上傳到 S3
aws s3 cp /backups/ s3://your-bucket/backups/ --recursive

# 清理舊備份 (30 天前)
find /backups -mtime +30 -delete
```

### 10.3 復原程序

```bash
#!/bin/bash
# restore.sh

# 從 S3 下載備份
aws s3 cp s3://your-bucket/backups/db_YYYYMMDD.dump /backups/

# 停止服務
docker-compose stop web celery

# 復原資料庫
pg_restore -h $DB_HOST -U $DB_USER -d $DB_NAME -c /backups/db_YYYYMMDD.dump

# 重啟服務
docker-compose up -d
```

### 10.4 RTO / RPO

| 指標 | 目標 | 說明 |
|------|------|------|
| **RTO** | 4 小時 | 復原時間目標 |
| **RPO** | 1 小時 | 復原點目標 (最多遺失 1 小時數據) |

---

## 11. 開發環境設置

### 11.1 系統需求

| 元件 | Windows | macOS | Linux |
|------|---------|-------|-------|
| Python | 3.11+ (官方安裝) | 3.11+ (Homebrew) | 3.11+ (apt/yum) |
| Node.js | 18+ (官方安裝) | 18+ (Homebrew) | 18+ (nvm) |
| Redis | Redis for Windows | brew install redis | apt install redis |
| Git | Git for Windows | Xcode CLI Tools | apt install git |

### 11.2 快速開始

```bash
# 1. Clone 專案
git clone https://github.com/your-org/agent-dating.git
cd agent-dating

# 2. 後端設置
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. 環境變數
cp .env.example .env
# 編輯 .env 設定 GROQ_API_KEY

# 4. 資料庫初始化
python manage.py migrate
python manage.py createsuperuser

# 5. 啟動 Redis (新終端)
redis-server

# 6. 啟動 Celery (新終端)
celery -A config worker -l info

# 7. 啟動 Django (新終端)
python manage.py runserver

# 8. 啟動前端 (新終端)
cd ../frontend
npx serve -p 3000

# 9. 訪問
# 前端: http://localhost:3000
# 後端: http://localhost:8000
# Admin: http://localhost:8000/admin
```

### 11.3 IDE 設定

#### VS Code 推薦擴展

```json
// .vscode/extensions.json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-python.debugpy",
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "ms-azuretools.vscode-docker"
  ]
}
```

#### VS Code 設定

```json
// .vscode/settings.json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/backend/venv/Scripts/python.exe",
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "editor.formatOnSave": true
}
```

### 11.4 測試帳號

| 帳號 | Email | 密碼 | 說明 |
|------|-------|------|------|
| Admin | amberh2616@gmail.com | 1234 | 管理員 |
| Maria | maria@test.com | 1234 | 測試用戶 |

---

## 12. 測試策略

### 12.1 測試金字塔

```
                    ┌───────────────┐
                    │    E2E Tests   │
                    │   (Cypress)    │
                    │      5%        │
                    └───────┬───────┘
                            │
              ┌─────────────┴─────────────┐
              │    Integration Tests       │
              │      (pytest-django)       │
              │           25%              │
              └─────────────┬─────────────┘
                            │
        ┌───────────────────┴───────────────────┐
        │            Unit Tests                  │
        │         (pytest, unittest)             │
        │              70%                       │
        └────────────────────────────────────────┘
```

### 12.2 單元測試

```python
# tests/test_matching_engine.py

import pytest
from apps.matching.engine import calculate_match_score

class TestMatchingEngine:

    def test_perfect_match(self):
        """完全相同的靈魂檔案應該得到高分"""
        profile = create_sample_profile()
        score = calculate_match_score(profile, profile)
        assert score.total_score >= 95

    def test_dealbreaker_detection(self):
        """底線衝突應該導致配對失敗"""
        profile_a = create_profile(core_values=['honesty'])
        profile_b = create_profile(dealbreakers=['honesty'])

        score = calculate_match_score(profile_a, profile_b)
        assert score.has_dealbreaker == True
        assert score.total_score == 0

    def test_worldview_similarity(self):
        """世界觀相似度計算"""
        profile_a = create_profile(worldview={'optimism': 80})
        profile_b = create_profile(worldview={'optimism': 70})

        similarity = calculate_worldview_similarity(profile_a, profile_b)
        assert similarity == 90  # 100 - |80-70| = 90
```

### 12.3 整合測試

```python
# tests/test_chat_api.py

import pytest
from rest_framework.test import APIClient

@pytest.mark.django_db
class TestChatAPI:

    @pytest.fixture
    def authenticated_client(self, user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    def test_start_conversation(self, authenticated_client, other_agent):
        """測試開始對話"""
        response = authenticated_client.post(
            f'/api/chat/start/{other_agent.id}/'
        )
        assert response.status_code == 200
        assert 'conversation_id' in response.data

    def test_send_message(self, authenticated_client, conversation):
        """測試發送訊息"""
        response = authenticated_client.post(
            f'/api/chat/conversations/{conversation.id}/send/',
            {'content': 'Hello!'}
        )
        assert response.status_code == 200
        assert response.data['content'] == 'Hello!'
```

### 12.4 執行測試

```bash
# 執行所有測試
pytest

# 執行特定模組
pytest tests/test_matching_engine.py

# 產生覆蓋率報告
pytest --cov=apps --cov-report=html

# 並行執行 (需要 pytest-xdist)
pytest -n auto
```

### 12.5 CI/CD Pipeline

```yaml
# .github/workflows/test.yml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test
        ports:
          - 5432:5432

      redis:
        image: redis:7
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-django pytest-cov

      - name: Run tests
        run: |
          cd backend
          pytest --cov=apps --cov-report=xml
        env:
          DATABASE_URL: postgres://test:test@localhost:5432/test
          REDIS_URL: redis://localhost:6379/0
          GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./backend/coverage.xml
```

---

## 附錄

### A. 環境變數完整列表

```env
# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
USE_SQLITE=True  # 開發用
DATABASE_URL=postgres://user:pass@host:5432/dbname  # 生產用

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1

# AI
GROQ_API_KEY=gsk_xxxx
GROQ_MODEL=llama-3.3-70b-versatile

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080

# JWT
JWT_ACCESS_TOKEN_LIFETIME=60  # 分鐘
JWT_REFRESH_TOKEN_LIFETIME=7  # 天
```

### B. 常見問題排查

| 問題 | 可能原因 | 解決方案 |
|------|---------|---------|
| AI 回覆延遲 | Celery worker 未啟動 | 啟動 celery -A config worker |
| WebSocket 連接失敗 | Daphne 未啟動 | 生產環境需獨立啟動 Daphne |
| 配對分數為 0 | Dealbreaker 衝突 | 檢查靈魂檔案底線設定 |
| 氣泡不顯示 | z-index 被覆蓋 | 確保 bubble-layer z-index 最高 |
| Avatar 載入失敗 | Habbo API 限流 | 增加請求間隔 |

### C. 性能調優建議

1. **資料庫**: 定期執行 VACUUM 和 ANALYZE
2. **Redis**: 設定適當的 maxmemory 和 eviction policy
3. **Celery**: 根據負載調整 worker 數量和 concurrency
4. **Nginx**: 啟用 gzip 壓縮和靜態檔案快取

---

**文件結束**

*最後更新: 2026-01-29*
*版本: 1.0*
