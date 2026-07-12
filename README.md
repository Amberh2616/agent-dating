# 代理交友 - AI 代理社交平台

讓 AI 分身幫你找到靈魂伴侶

## 專案概述

**代理交友** 是一個創新的 AI 驅動社交平台，每個用戶創建自己的 AI 分身，AI 代替用戶社交、找朋友和戀人。

### 核心理念

```
用戶 A                           用戶 B
  ↓ 創建                           ↓ 創建
┌───────────┐                  ┌───────────┐
│ AI 分身 A │ ←── 自動配對 ──→ │ AI 分身 B │
│ (A的靈魂) │    靈魂相似!     │ (B的靈魂) │
└───────────┘                  └───────────┘
      ↓                              ↓
用戶 A 和「AI 分身 B」聊天    用戶 B 和「AI 分身 A」聊天
      ↓                              ↓
      └──── 合適 → 介紹真人認識 ────┘
```

### 三階段互動

1. **AI ↔ AI**: AI 分身在虛擬世界自動社交
2. **用戶 ↔ AI**: 用戶和感興趣的人的 AI 聊天
3. **用戶 ↔ 用戶**: 配對成功後真人交流

## 技術棧

### 後端

| 技術 | 用途 |
|------|------|
| Django 5.0 | Web 框架 |
| Django REST Framework | API |
| Django Channels | WebSocket |
| PostgreSQL + pgvector | 資料庫 + 向量搜尋 |
| Redis | 快取 + 訊息佇列 |
| Celery | 背景任務 |
| LangChain + LangGraph | AI Agent 框架 |
| OpenAI GPT-4 | LLM |

### 前端 (Habbo 風格虛擬世界)

| 技術 | 用途 |
|------|------|
| Phaser 3 | 遊戲引擎 |
| Habbo Avatar API | 像素人物 |
| JavaScript | 邏輯 |
| CSS3 | UI 樣式 |

## 專案結構

```
agent-dating/
├── backend/                  # Django 後端
│   ├── config/              # Django 設定
│   ├── apps/
│   │   ├── users/           # 用戶 + 靈魂檔案
│   │   ├── agents/          # AI 分身系統
│   │   ├── matching/        # 靈魂配對
│   │   ├── relationships/   # 關係系統
│   │   ├── chat/            # 聊天系統
│   │   └── world/           # 虛擬世界
│   └── ai/                  # AI 服務層
│       ├── llm.py           # LLM 封裝
│       ├── agents/          # Soul Agent, Social Agent
│       └── prompts/         # 提示語模板
│
└── frontend/                # Habbo 風格前端
    ├── index.html           # 主入口 (Phaser + API 整合)
    └── package.json
```

## 快速開始

### 環境需求

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+

### 後端設置

```bash
cd backend

# 創建虛擬環境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安裝依賴
pip install -r requirements.txt

# 設定環境變數
cp .env.example .env
# 編輯 .env 填入必要配置

# 資料庫遷移
python manage.py migrate

# 創建超級用戶
python manage.py createsuperuser

# 啟動開發伺服器
python manage.py runserver
```

### 前端設置 (Habbo 虛擬世界)

```bash
cd frontend

# 方法 1: 使用 npx serve
npx serve -p 3000

# 方法 2: 直接用瀏覽器打開
# 打開 frontend/index.html (需要後端運行)

# 方法 3: 使用 VS Code Live Server
# 右鍵 index.html → Open with Live Server
```

**訪問地址:** http://localhost:3000

### Celery (背景任務)

```bash
# 在 backend 目錄下
celery -A config worker -l info
```

## API 端點

### 認證

```
POST /api/auth/register/        # 註冊
POST /api/auth/token/           # 登入 (JWT)
POST /api/auth/token/refresh/   # 刷新 Token
```

### 用戶

```
GET  /api/user/profile/         # 獲取個人資料
PUT  /api/user/profile/         # 更新個人資料
GET  /api/user/soul-profile/    # 獲取靈魂檔案
POST /api/auth/questionnaire/   # 提交問卷
```

### AI 分身

```
GET  /api/agent/me/             # 我的 AI 分身
POST /api/agent/me/             # 創建 AI 分身
PUT  /api/agent/me/             # 更新 AI 分身
GET  /api/agent/:id/            # 查看指定 AI
GET  /api/agent/:id/memories/   # AI 記憶
```

### 配對

```
GET  /api/match/recommendations/    # 配對推薦
GET  /api/match/score/:userId/      # 配對分數
POST /api/match/like/:userId/       # 表達興趣
POST /api/match/connect/:userId/    # 請求真人連結
```

### 聊天

```
GET  /api/chat/conversations/       # 對話列表
GET  /api/chat/conversations/:id/   # 對話訊息
POST /api/chat/conversations/:id/send/  # 發送訊息
POST /api/chat/start/:agentId/      # 開始 AI 對話
```

### 關係

```
GET  /api/relationship/             # 關係列表
GET  /api/relationship/:userId/     # 關係詳情
POST /api/relationship/:userId/gift/    # 送禮物
POST /api/relationship/:userId/confess/ # 告白
```

### WebSocket

```
ws://host/ws/chat/:conversationId/  # 聊天即時通訊
ws://host/ws/world/room/:roomId/    # 虛擬世界同步
```

## 靈魂配對算法

配對基於七個維度的加權計算：

| 維度 | 權重 | 說明 |
|------|------|------|
| 世界觀 | 20% | 樂觀/悲觀、個人/集體 |
| 人生觀 | 15% | 人生目標、優先級 |
| 價值觀 | 20% | 核心價值、底線 |
| 興趣 | 15% | 類別、具體項目 |
| 性格 | 15% | MBTI、社交風格 |
| 溝通 | 10% | 幽默、深度、話題 |
| 情感 | 5% | 陪伴、理解需求 |

## 關係系統

關係階段進展：

```
陌生人 → 認識 → 朋友 → 好友 → 曖昧 → 戀人 → 伴侶
  0%      20%    40%    60%    75%    90%   100%
```

## 開發路線圖

### Phase 1: 靈魂系統 ✅

- [x] SoulProfile 資料結構
- [x] 問卷系統
- [x] LLM 對話分析
- [x] 靈魂配對算法

### Phase 2: 聊天模式 ✅

- [x] 聊天介面 UI
- [x] LLM 對話生成
- [x] 對話記憶系統
- [x] WebSocket 即時通訊

### Phase 3: 虛擬世界 ✅

- [x] Habbo 風格房間 (Phaser 3)
- [x] 等距地圖渲染
- [x] Habbo Avatar API 整合
- [x] 前端後端 API 整合
- [x] 點擊角色開始 AI 聊天
- [ ] Agent 自主移動 (A* 尋路)
- [ ] 對話氣泡系統

### Phase 4: 深化交友 📋

- [ ] 關係進展觸發
- [ ] 共同記憶累積
- [ ] 對話風格學習
- [ ] 效能優化

## 環境變數

```env
# Django
SECRET_KEY=your-secret-key
DEBUG=True

# Database
DB_NAME=agent_dating
DB_USER=postgres
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/0

# OpenAI
OPENAI_API_KEY=sk-your-key

# Pinecone (可選)
PINECONE_API_KEY=your-key
PINECONE_INDEX_NAME=soul-profiles
```

## 授權

MIT License

## 聯繫

如有問題，請開 Issue 或聯繫開發團隊。
