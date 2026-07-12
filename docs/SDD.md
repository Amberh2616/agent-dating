# Software Design Document (SDD)
## Agent-Dating: AI 代理社交平台

**版本**: 1.0
**日期**: 2026-01-29
**作者**: Claude Code AI

---

## 目錄

1. [簡介](#1-簡介)
2. [系統概述](#2-系統概述)
3. [架構設計](#3-架構設計)
4. [模組設計](#4-模組設計)
5. [資料庫設計](#5-資料庫設計)
6. [API 設計](#6-api-設計)
7. [即時通訊設計](#7-即時通訊設計)
8. [AI 系統設計](#8-ai-系統設計)
9. [安全性設計](#9-安全性設計)
10. [附錄](#10-附錄)

---

## 1. 簡介

### 1.1 文件目的

本文件為 Agent-Dating 專案的軟體設計文件 (Software Design Document)，詳述系統架構、模組設計、資料模型及介面規格，供開發團隊參考實作。

### 1.2 專案背景

Agent-Dating 是一個創新的 AI 驅動社交平台。用戶創建自己的 AI 分身，由 AI 代替用戶進行社交、尋找朋友和潛在伴侶，基於靈魂（三觀、興趣、性格）進行深度配對。

### 1.3 核心概念

```
用戶創建 AI 分身 → AI 自動社交 → 用戶與感興趣者的 AI 聊天 → 配對成功認識真人
```

### 1.4 範圍

本文件涵蓋：
- 後端系統 (Django + DRF)
- 前端系統 (Phaser 3 + Habbo 風格)
- AI 服務層 (LangChain + Groq)
- 即時通訊 (Django Channels + WebSocket)
- 背景任務系統 (Celery + APScheduler)

### 1.5 術語定義

| 術語 | 定義 |
|------|------|
| Agent | AI 分身，代表用戶進行社交的虛擬角色 |
| Soul Profile | 靈魂檔案，包含用戶的三觀、興趣、性格等 8 個維度 |
| Memory | Agent 的記憶，包括觀察、對話、情感等 |
| Reflection | Agent 從記憶中生成的高層次反思和洞察 |
| Intent | Agent 的短期目標和意圖 |
| Dealbreaker | 配對時的底線衝突，導致配對失敗 |

---

## 2. 系統概述

### 2.1 系統目標

1. **自動化社交**: AI 代替用戶進行初步社交篩選
2. **深度配對**: 基於靈魂相容性的 7 維度配對算法
3. **自然互動**: AI 分身具有記憶、情緒、反思能力
4. **沉浸體驗**: Habbo 風格虛擬世界視覺呈現

### 2.2 系統邊界

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent-Dating System                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│   ┌───────────────┐      ┌───────────────┐                  │
│   │   Frontend    │ ←──→ │   Backend     │                  │
│   │  (Phaser 3)   │      │  (Django)     │                  │
│   └───────────────┘      └───────┬───────┘                  │
│                                   │                           │
│                          ┌────────┴────────┐                 │
│                          │                 │                 │
│                   ┌──────┴──────┐  ┌──────┴──────┐          │
│                   │ AI Service  │  │   Celery    │          │
│                   │  (Groq)     │  │  Workers    │          │
│                   └─────────────┘  └─────────────┘          │
│                                                               │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
   ┌──────────┐      ┌──────────────┐      ┌──────────┐
   │ Habbo    │      │  PostgreSQL  │      │  Redis   │
   │ Avatar   │      │   Database   │      │  Queue   │
   │   API    │      └──────────────┘      └──────────┘
   └──────────┘
```

### 2.3 用戶角色

| 角色 | 描述 | 權限 |
|------|------|------|
| 訪客 | 未註冊用戶 | 查看首頁 |
| 一般用戶 | 已註冊並完成問卷 | 所有功能 |
| Premium 用戶 | 付費用戶 | 進階配對、無限對話 |
| 管理員 | 系統管理者 | Django Admin 後台 |

---

## 3. 架構設計

### 3.1 整體架構圖

```
┌────────────────────────────────────────────────────────────────┐
│                         PRESENTATION LAYER                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           Frontend (Phaser 3 + Vanilla JS)               │  │
│  │  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │  │
│  │  │ RoomScene   │  │ ChatUI       │  │ AvatarManager  │  │  │
│  │  │ (Isometric) │  │ (WebSocket)  │  │ (Habbo API)    │  │  │
│  │  └─────────────┘  └──────────────┘  └────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────┬──────────────────────────────────┘
                              │ HTTP/WebSocket
┌─────────────────────────────▼──────────────────────────────────┐
│                         API GATEWAY LAYER                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Django REST Framework + Channels             │  │
│  │  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │  │
│  │  │ REST API    │  │ WebSocket    │  │ JWT Auth       │  │  │
│  │  │ ViewSets    │  │ Consumers    │  │ Middleware     │  │  │
│  │  └─────────────┘  └──────────────┘  └────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────┬──────────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────────┐
│                         BUSINESS LOGIC LAYER                    │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐  │
│  │   users    │ │   agents   │ │   chat     │ │  matching  │  │
│  │    App     │ │    App     │ │    App     │ │    App     │  │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘  │
│  ┌────────────┐ ┌────────────┐ ┌────────────────────────────┐ │
│  │relationships│ │   world   │ │      AI Service Layer      │ │
│  │    App     │ │    App     │ │  (LLM, Memory, Reflection) │ │
│  └────────────┘ └────────────┘ └────────────────────────────┘ │
└─────────────────────────────┬──────────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────────┐
│                         DATA ACCESS LAYER                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Django ORM + Models                    │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────┬──────────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────────┐
│                         INFRASTRUCTURE LAYER                    │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐               │
│  │ PostgreSQL │  │   Redis    │  │   Groq     │               │
│  │  Database  │  │   Cache    │  │    API     │               │
│  └────────────┘  └────────────┘  └────────────┘               │
└────────────────────────────────────────────────────────────────┘
```

### 3.2 Django 應用架構

```
backend/
├── config/                    # Django 設定
│   ├── settings.py           # 主設定檔
│   ├── urls.py               # URL 路由
│   ├── celery.py             # Celery 設定
│   └── asgi.py               # ASGI 入口 (WebSocket)
│
├── apps/                      # 業務應用
│   ├── users/                # 用戶與靈魂檔案
│   ├── agents/               # AI 分身系統
│   ├── chat/                 # 聊天系統
│   ├── matching/             # 配對系統
│   ├── relationships/        # 關係系統
│   ├── world/                # 虛擬世界
│   └── translations/         # 多語言
│
└── ai/                        # AI 服務層
    ├── llm.py                # LLM 服務
    ├── agents/               # AI Agent 實現
    └── prompts/              # 提示詞模板
```

### 3.3 設計原則

| 原則 | 實現方式 |
|------|----------|
| **單一職責** | 每個 App 負責單一業務領域 |
| **開閉原則** | 服務層使用介面抽象，支援擴展 |
| **依賴反轉** | 使用依賴注入和服務定位器模式 |
| **介面隔離** | API 分層：REST + WebSocket |

---

## 4. 模組設計

### 4.1 users 模組

#### 職責
- 用戶身份認證與註冊
- 靈魂檔案 (Soul Profile) 管理
- 15 題問卷系統
- 多語言偏好

#### 類別圖

```
┌─────────────────────────────────────────┐
│              User                        │
├─────────────────────────────────────────┤
│ - id: UUID                              │
│ - email: str (unique)                   │
│ - username: str                         │
│ - avatar_url: str                       │
│ - preferred_language: str               │
│ - is_verified: bool                     │
│ - is_premium: bool                      │
│ - onboarding_completed: bool            │
├─────────────────────────────────────────┤
│ + create_user()                         │
│ + update_profile()                      │
│ + complete_onboarding()                 │
└───────────────┬─────────────────────────┘
                │ 1:1
                ▼
┌─────────────────────────────────────────┐
│           SoulProfile                    │
├─────────────────────────────────────────┤
│ - worldview: JSONField                  │
│ - lifeview: JSONField                   │
│ - values: JSONField                     │
│ - interests: JSONField                  │
│ - personality: JSONField                │
│ - communication_style: JSONField        │
│ - emotional_needs: JSONField            │
│ - love_style: JSONField                 │
│ - soul_vector: JSONField (1536 dim)     │
├─────────────────────────────────────────┤
│ + to_dict()                             │
│ + update_from_questionnaire()           │
│ + generate_soul_vector()                │
└─────────────────────────────────────────┘
```

#### 靈魂檔案 8 維度

```json
{
  "worldview": {
    "optimism": 0-100,
    "spirituality": 0-100,
    "individualism": 0-100,
    "changeOriented": 0-100
  },
  "lifeview": {
    "purpose": ["追求快樂", "實現自我"],
    "priorities": ["家庭", "事業", "自由"],
    "lifeStage": "探索期|奮鬥期|穩定期|享受期"
  },
  "values": {
    "core": ["誠實", "創意", "勇氣"],
    "dealbreakers": ["欺騙", "冷漠"],
    "importanceRank": { "love": 1-5, "friendship": 1-5, ... }
  },
  "interests": {
    "categories": ["藝術", "科技"],
    "specific": { "music": [...], "movies": [...] },
    "depth": "casual|enthusiast|expert"
  },
  "personality": {
    "mbti": "ENFP",
    "traits": { "introversion": 0-100, ... },
    "socialStyle": "傾聽者|分享者|引導者"
  },
  "communication_style": {
    "humor": 0-100,
    "depth": 0-100,
    "emotionality": 0-100,
    "preferredTopics": [...]
  },
  "emotional_needs": {
    "companionship": 0-100,
    "validation": 0-100,
    "stimulation": 0-100,
    "understanding": 0-100
  },
  "love_style": {
    "attachmentType": "secure|anxious|avoidant",
    "loveLanguage": ["肯定的言語", "精心時刻"],
    "romanticLevel": 0-100,
    "jealousy": 0-100
  }
}
```

### 4.2 agents 模組

#### 職責
- AI 分身創建與管理
- 記憶流系統 (Memory Stream)
- 反思與洞察 (Reflection)
- 意圖與目標管理 (Intent)
- 情緒動態系統

#### 類別圖

```
┌────────────────────────────────────────────┐
│                  Agent                      │
├────────────────────────────────────────────┤
│ - id: UUID                                 │
│ - user: User (1:1)                         │
│ - name: str                                │
│ - avatar_look: str (Habbo code)            │
│ - bio: str                                 │
│ - emotion_state: JSONField                 │
│ - emotion_baseline: JSONField              │
│ - current_emotion: str                     │
│ - current_location: JSONField              │
│ - last_chat_message: str                   │
│ - is_online: bool                          │
│ - is_autonomous: bool                      │
├────────────────────────────────────────────┤
│ + get_emotion_state(): dict                │
│ + get_emotion_baseline(): dict             │
│ + update_emotion(changes, decay_rate)      │
│ + get_emotion_description(): str           │
│ + _derive_emotion_label(): str             │
└───────────────┬────────────────────────────┘
                │ 1:N
                ▼
┌────────────────────────────────────────────┐
│                 Memory                      │
├────────────────────────────────────────────┤
│ - id: UUID                                 │
│ - agent: Agent (FK)                        │
│ - type: observation|reflection|plan|       │
│         conversation|emotion               │
│ - content: TextField                       │
│ - importance: int (1-10)                   │
│ - related_agents: JSONField                │
│ - location: JSONField                      │
│ - emotion: str                             │
│ - embedding: JSONField (1536 dim)          │
│ - access_count: int                        │
│ - last_accessed: datetime                  │
├────────────────────────────────────────────┤
│ + retrieve_for_decision()                  │
│ + decay_importance()                       │
└────────────────────────────────────────────┘
```

#### 情緒系統設計

```
┌──────────────────────────────────────────────┐
│              情緒動態系統                     │
├──────────────────────────────────────────────┤
│                                              │
│  emotion_state (即時情緒)                     │
│  ├─ happiness: 0-100                        │
│  ├─ energy: 0-100                           │
│  ├─ stress: 0-100                           │
│  └─ openness: 0-100                         │
│                                              │
│  emotion_baseline (性格基準線)                │
│  └─ 根據 personality 計算                    │
│                                              │
│  更新機制:                                    │
│  1. 事件影響 → 即時變化                       │
│  2. 衰減回歸 → 慢慢回到基準線 (decay=0.1)    │
│                                              │
│  標籤推導:                                    │
│  stress > 70 → stressed                      │
│  happiness > 70 & energy > 60 → excited      │
│  happiness > 60 → happy                      │
│  happiness < 30 → sad                        │
│  energy < 30 → tired                         │
│  其他 → neutral                              │
│                                              │
└──────────────────────────────────────────────┘
```

### 4.3 chat 模組

#### 職責
- 對話管理
- 訊息收發
- 三模式聊天系統 (AI 代聊 / 用戶親自 / 暫停)
- 對話摘要與報告

#### 類別圖

```
┌────────────────────────────────────────────┐
│              Conversation                   │
├────────────────────────────────────────────┤
│ - id: UUID                                 │
│ - conversation_type: user_to_agent |       │
│                       agent_to_agent |     │
│                       user_to_user         │
│ - mode: ai | user | paused                 │
│ - user_participant: User (FK, nullable)    │
│ - agent_participant: Agent (FK, nullable)  │
│ - other_agent: Agent (FK, nullable)        │
│ - other_user: User (FK, nullable)          │
│ - message_count: int                       │
│ - last_message_at: datetime                │
│ - is_active: bool                          │
├────────────────────────────────────────────┤
│ + get_recent_messages(limit)               │
│ + switch_mode(new_mode)                    │
│ + archive()                                │
└───────────────┬────────────────────────────┘
                │ 1:N
                ▼
┌────────────────────────────────────────────┐
│                 Message                     │
├────────────────────────────────────────────┤
│ - id: UUID                                 │
│ - conversation: Conversation (FK)          │
│ - sender_type: user | agent                │
│ - sender_user: User (FK, nullable)         │
│ - sender_agent: Agent (FK, nullable)       │
│ - message_type: text | image | gift | action│
│ - content: TextField                       │
│ - emotion: str                             │
│ - is_ai_generated: bool                    │
│ - is_read: bool                            │
└────────────────────────────────────────────┘
```

#### 三模式聊天系統

```
┌─────────────────────────────────────────────┐
│           三模式聊天系統設計                  │
├─────────────────────────────────────────────┤
│                                             │
│  Mode: AI (AI 代聊)                          │
│  ├─ AI 自動和配對對象聊天                     │
│  ├─ 定期觸發 (每小時檢查)                     │
│  ├─ 生成對話摘要報告                          │
│  └─ 用戶可隨時查看報告                        │
│                                             │
│  Mode: USER (用戶親自)                        │
│  ├─ 用戶親自輸入訊息                          │
│  ├─ AI 仍會回覆 (對方的 AI)                   │
│  └─ 用戶完全控制對話                          │
│                                             │
│  Mode: PAUSED (暫停)                         │
│  ├─ 暫時停止對話                             │
│  └─ 不會觸發任何 AI 回覆                      │
│                                             │
│  狀態轉換:                                    │
│  AI ←→ USER ←→ PAUSED                       │
│  (任意狀態可互相切換)                         │
│                                             │
└─────────────────────────────────────────────┘
```

### 4.4 matching 模組

#### 職責
- 配對分數計算
- 配對推薦引擎
- Dealbreaker 檢測

#### 7 維度配對算法

```
┌─────────────────────────────────────────────────┐
│              配對算法設計                        │
├─────────────────────────────────────────────────┤
│                                                 │
│  權重配置:                                       │
│  ├─ Worldview (世界觀):    20%                  │
│  ├─ Lifeview (人生觀):     15%                  │
│  ├─ Values (價值觀):       20%                  │
│  ├─ Interests (興趣):      15%                  │
│  ├─ Personality (性格):    15%                  │
│  ├─ Communication (對話):  10%                  │
│  └─ Emotional (情感):       5%                  │
│                                                 │
│  Dealbreaker 檢查:                               │
│  if (user_a.dealbreakers ∩ user_b.core_values)  │
│     → 配對失敗，分數為 0                         │
│                                                 │
│  總分計算:                                       │
│  total = Σ(similarity[dim] × weight[dim])       │
│  範圍: 0-100                                    │
│                                                 │
│  亮點提取:                                       │
│  取前 3 個相似度 >= 70% 的維度                   │
│                                                 │
└─────────────────────────────────────────────────┘
```

### 4.5 relationships 模組

#### 職責
- 關係進展追蹤
- 關係階段管理
- 虛擬禮物系統

#### 7 階段關係系統

```
┌─────────────────────────────────────────────────┐
│              關係階段設計                        │
├─────────────────────────────────────────────────┤
│                                                 │
│  Stage 0: stranger (陌生人)     closeness: 0    │
│      ↓                                          │
│  Stage 1: acquaintance (認識)   closeness: 20   │
│      ↓                                          │
│  Stage 2: friend (朋友)         closeness: 40   │
│      ↓                                          │
│  Stage 3: close_friend (好友)   closeness: 60   │
│      ↓                                          │
│  Stage 4: crush (曖昧)          closeness: 75   │
│      ↓                                          │
│  Stage 5: lover (戀人)          closeness: 90   │
│      ↓                                          │
│  Stage 6: partner (伴侶)        closeness: 100  │
│                                                 │
│  進展條件:                                       │
│  - 互動次數達標                                  │
│  - 親密度達到閾值                                │
│  - 雙方有意願 (romantic > 50)                   │
│                                                 │
└─────────────────────────────────────────────────┘
```

### 4.6 world 模組

#### 職責
- 虛擬房間管理
- Agent 位置追蹤
- 世界事件廣播

#### 房間設計

```
┌─────────────────────────────────────────────────┐
│                Room                              │
├─────────────────────────────────────────────────┤
│ - id: UUID                                      │
│ - name: str                                     │
│ - room_type: public | cafe | plaza | park |     │
│              bar | library | gym | private      │
│ - owner: User (FK, nullable)                    │
│ - width: int                                    │
│ - height: int                                   │
│ - floor_plan: JSONField (2D walkable tiles)     │
│ - spawn_points: JSONField                       │
│ - furniture: JSONField                          │
│ - max_capacity: int                             │
└─────────────────────────────────────────────────┘
```

---

## 5. 資料庫設計

### 5.1 ER 圖

```
┌─────────────────────────────────────────────────────────────────┐
│                        Entity Relationship Diagram              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌──────────┐ 1:1 ┌─────────────┐                             │
│   │   User   │────→│ SoulProfile │                             │
│   └────┬─────┘     └─────────────┘                             │
│        │                                                        │
│        │ 1:1                                                    │
│        ▼                                                        │
│   ┌──────────┐                                                  │
│   │  Agent   │                                                  │
│   └────┬─────┘                                                  │
│        │                                                        │
│        ├───── 1:N ─────→ Memory                                 │
│        ├───── 1:N ─────→ AgentReflection                        │
│        ├───── 1:N ─────→ AgentIntent                            │
│        ├───── 1:N ─────→ AgentAction                            │
│        ├───── 1:N ─────→ DailyPlan                              │
│        ├───── 1:N ─────→ InteractionLog                         │
│        └───── 1:1 ─────→ AgentPosition                          │
│                                                                 │
│   User ←──── N:N ────→ User                                     │
│        via Relationship                                         │
│        via MatchScore                                           │
│        via MatchInterest                                        │
│        via MatchRequest                                         │
│                                                                 │
│   Conversation                                                   │
│        ├───── N:1 ─────→ User (user_participant)                │
│        ├───── N:1 ─────→ Agent (agent_participant)              │
│        ├───── N:1 ─────→ Agent (other_agent)                    │
│        ├───── 1:N ─────→ Message                                │
│        ├───── 1:1 ─────→ ChatContext                            │
│        └───── 1:N ─────→ ConversationSummary                    │
│                                                                 │
│   Room                                                           │
│        ├───── N:1 ─────→ User (owner)                           │
│        ├───── 1:N ─────→ AgentPosition                          │
│        ├───── 1:N ─────→ WorldEvent                             │
│        └───── 1:N ─────→ InteractionLog                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 核心資料表

#### 5.2.1 users_user

| 欄位 | 類型 | 約束 | 說明 |
|------|------|------|------|
| id | UUID | PK | 主鍵 |
| email | VARCHAR(255) | UNIQUE, NOT NULL | 電子郵件 |
| username | VARCHAR(150) | NOT NULL | 用戶名稱 |
| password | VARCHAR(128) | NOT NULL | 密碼雜湊 |
| avatar_url | VARCHAR(500) | NULL | 頭像 URL |
| bio | TEXT | NULL | 自我介紹 |
| gender | VARCHAR(20) | NULL | 性別 |
| birthday | DATE | NULL | 生日 |
| location | VARCHAR(100) | NULL | 所在地 |
| preferred_language | VARCHAR(10) | DEFAULT 'zh-hant' | 語言偏好 |
| is_verified | BOOLEAN | DEFAULT FALSE | 是否驗證 |
| is_premium | BOOLEAN | DEFAULT FALSE | 是否付費 |
| onboarding_completed | BOOLEAN | DEFAULT FALSE | 是否完成引導 |
| created_at | DATETIME | AUTO | 創建時間 |
| updated_at | DATETIME | AUTO | 更新時間 |

#### 5.2.2 users_soulprofile

| 欄位 | 類型 | 約束 | 說明 |
|------|------|------|------|
| id | UUID | PK | 主鍵 |
| user_id | UUID | FK, UNIQUE | 關聯用戶 |
| worldview | JSONB | NOT NULL | 世界觀 |
| lifeview | JSONB | NOT NULL | 人生觀 |
| values | JSONB | NOT NULL | 價值觀 |
| interests | JSONB | NOT NULL | 興趣 |
| personality | JSONB | NOT NULL | 性格 |
| communication_style | JSONB | NOT NULL | 對話風格 |
| emotional_needs | JSONB | NOT NULL | 情感需求 |
| love_style | JSONB | NOT NULL | 戀愛特質 |
| soul_vector | JSONB | NULL | 靈魂向量 (1536 維) |

#### 5.2.3 agents_agent

| 欄位 | 類型 | 約束 | 說明 |
|------|------|------|------|
| id | UUID | PK | 主鍵 |
| user_id | UUID | FK, UNIQUE | 關聯用戶 |
| name | VARCHAR(100) | NOT NULL | Agent 名稱 |
| avatar_look | VARCHAR(500) | NULL | Habbo look code |
| bio | TEXT | NULL | 簡介 |
| emotion_state | JSONB | NOT NULL | 即時情緒 |
| emotion_baseline | JSONB | NOT NULL | 情緒基準線 |
| current_emotion | VARCHAR(50) | NULL | 情緒標籤 |
| current_location | JSONB | NULL | 當前位置 |
| current_action | VARCHAR(50) | NULL | 當前動作 |
| last_chat_message | VARCHAR(500) | NULL | 最後訊息 |
| last_chat_time | DATETIME | NULL | 最後聊天時間 |
| is_online | BOOLEAN | DEFAULT FALSE | 是否在線 |
| is_autonomous | BOOLEAN | DEFAULT TRUE | 是否自主 |

#### 5.2.4 agents_memory

| 欄位 | 類型 | 約束 | 說明 |
|------|------|------|------|
| id | UUID | PK | 主鍵 |
| agent_id | UUID | FK, INDEX | 關聯 Agent |
| type | VARCHAR(20) | NOT NULL, INDEX | 記憶類型 |
| content | TEXT | NOT NULL | 內容 |
| importance | INTEGER | NOT NULL, INDEX | 重要性 (1-10) |
| related_agents | JSONB | DEFAULT [] | 相關 Agent IDs |
| location | JSONB | NULL | 發生位置 |
| emotion | VARCHAR(50) | NULL | 當時情緒 |
| embedding | JSONB | NULL | 向量嵌入 |
| access_count | INTEGER | DEFAULT 0 | 訪問次數 |
| last_accessed | DATETIME | AUTO | 最後訪問 |
| created_at | DATETIME | AUTO, INDEX | 創建時間 |

**索引設計:**
```sql
CREATE INDEX idx_memory_agent_type ON agents_memory(agent_id, type);
CREATE INDEX idx_memory_agent_importance ON agents_memory(agent_id, importance);
CREATE INDEX idx_memory_agent_created ON agents_memory(agent_id, created_at DESC);
```

#### 5.2.5 chat_conversation

| 欄位 | 類型 | 約束 | 說明 |
|------|------|------|------|
| id | UUID | PK | 主鍵 |
| conversation_type | VARCHAR(20) | NOT NULL | 對話類型 |
| mode | VARCHAR(10) | DEFAULT 'ai' | 聊天模式 |
| user_participant_id | UUID | FK, NULL | 用戶參與者 |
| agent_participant_id | UUID | FK, NULL | Agent 參與者 |
| other_agent_id | UUID | FK, NULL | 對方 Agent |
| other_user_id | UUID | FK, NULL | 對方用戶 |
| message_count | INTEGER | DEFAULT 0 | 訊息數 |
| last_message_preview | VARCHAR(200) | NULL | 最後訊息預覽 |
| last_message_at | DATETIME | NULL, INDEX | 最後訊息時間 |
| is_active | BOOLEAN | DEFAULT TRUE | 是否活躍 |
| is_archived | BOOLEAN | DEFAULT FALSE | 是否封存 |

#### 5.2.6 matching_matchscore

| 欄位 | 類型 | 約束 | 說明 |
|------|------|------|------|
| id | UUID | PK | 主鍵 |
| user_a_id | UUID | FK, INDEX | 用戶 A |
| user_b_id | UUID | FK, INDEX | 用戶 B |
| total_score | FLOAT | NOT NULL | 總分 (0-100) |
| worldview_score | FLOAT | NOT NULL | 世界觀分數 |
| lifeview_score | FLOAT | NOT NULL | 人生觀分數 |
| values_score | FLOAT | NOT NULL | 價值觀分數 |
| interests_score | FLOAT | NOT NULL | 興趣分數 |
| personality_score | FLOAT | NOT NULL | 性格分數 |
| communication_score | FLOAT | NOT NULL | 對話分數 |
| emotional_score | FLOAT | NOT NULL | 情感分數 |
| highlights | JSONB | DEFAULT [] | 亮點列表 |
| has_dealbreaker | BOOLEAN | DEFAULT FALSE | 是否有底線衝突 |
| dealbreaker_reason | TEXT | NULL | 衝突原因 |
| created_at | DATETIME | AUTO | 創建時間 |

**唯一約束與索引:**
```sql
ALTER TABLE matching_matchscore
  ADD CONSTRAINT unique_user_pair UNIQUE (user_a_id, user_b_id);

CREATE INDEX idx_match_user_a_score ON matching_matchscore(user_a_id, total_score DESC);
CREATE INDEX idx_match_user_b_score ON matching_matchscore(user_b_id, total_score DESC);
```

---

## 6. API 設計

### 6.1 API 概述

- **基礎 URL**: `http://localhost:8000/api`
- **認證方式**: JWT Bearer Token
- **格式**: JSON
- **分頁**: `?page=1&page_size=20`

### 6.2 認證 API

#### POST /auth/token/
獲取 JWT Token

**Request:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response (200):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### POST /auth/token/refresh/
刷新 Token

**Request:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response (200):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### 6.3 用戶 API

#### GET /user/profile/
獲取個人資料

**Response (200):**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "username": "johndoe",
  "avatar_url": "https://...",
  "bio": "自我介紹",
  "preferred_language": "zh-hant",
  "is_premium": false,
  "onboarding_completed": true
}
```

#### GET /user/soul-profile/
獲取靈魂檔案

**Response (200):**
```json
{
  "worldview": { "optimism": 75, ... },
  "lifeview": { "purpose": [...], ... },
  "values": { "core": [...], ... },
  "interests": { "categories": [...], ... },
  "personality": { "mbti": "ENFP", ... },
  "communication_style": { "humor": 72, ... },
  "emotional_needs": { "companionship": 78, ... },
  "love_style": { "attachmentType": "secure", ... }
}
```

### 6.4 Agent API

#### GET /agent/me/
獲取我的 AI 分身

**Response (200):**
```json
{
  "id": "uuid",
  "name": "Amber",
  "avatar_look": "hd-180-1.hr-828-61.ch-210-66",
  "bio": "熱愛藝術和旅行的設計師",
  "emotion_state": {
    "happiness": 65,
    "energy": 70,
    "stress": 25,
    "openness": 75
  },
  "current_emotion": "happy",
  "is_online": true
}
```

#### GET /agent/{agent_id}/memories/
獲取 Agent 的記憶列表

**Query Parameters:**
- `type`: 記憶類型篩選 (observation, conversation, etc.)
- `importance_min`: 最低重要性
- `limit`: 返回數量 (default: 20)

**Response (200):**
```json
{
  "memories": [
    {
      "id": "uuid",
      "type": "conversation",
      "content": "Mike 喜歡討論科技和遊戲",
      "importance": 7,
      "emotion": "happy",
      "created_at": "2026-01-28T10:30:00Z"
    }
  ]
}
```

### 6.5 聊天 API

#### POST /chat/start/{agent_id}/
開始與 Agent 對話

**Response (200):**
```json
{
  "conversation_id": "uuid",
  "created": true,
  "mode": "user",
  "agent": {
    "id": "uuid",
    "name": "Mike",
    "avatar_look": "..."
  }
}
```

#### POST /chat/conversations/{conversation_id}/send/
發送訊息

**Request:**
```json
{
  "content": "嗨，你最近在忙什麼？"
}
```

**Response (200):**
```json
{
  "message_id": "uuid",
  "content": "嗨，你最近在忙什麼？",
  "sender_type": "user",
  "created_at": "2026-01-28T10:35:00Z"
}
```

#### POST /chat/conversations/{conversation_id}/mode/
切換聊天模式

**Request:**
```json
{
  "mode": "ai"
}
```

**Response (200):**
```json
{
  "conversation_id": "uuid",
  "mode": "ai",
  "mode_label": "AI 代聊",
  "message": "已切換至 AI 代聊模式"
}
```

### 6.6 配對 API

#### GET /match/recommendations/
獲取配對推薦

**Response (200):**
```json
{
  "recommendations": [
    {
      "user_id": "uuid",
      "username": "Jane",
      "match_score": 85,
      "highlights": ["都重視自由", "共同喜歡音樂", "性格互補"],
      "breakdown": {
        "worldview": 88,
        "lifeview": 82,
        "values": 90,
        "interests": 85,
        "personality": 78,
        "communication": 80,
        "emotional": 75
      },
      "has_dealbreaker": false,
      "agent": {
        "id": "uuid",
        "name": "Jane's AI",
        "avatar_look": "..."
      }
    }
  ]
}
```

### 6.7 完整 API 端點列表

| 方法 | 端點 | 說明 |
|------|------|------|
| POST | /auth/register/ | 用戶註冊 |
| POST | /auth/token/ | 登入獲取 Token |
| POST | /auth/token/refresh/ | 刷新 Token |
| GET | /auth/questionnaire/ | 獲取問卷題目 |
| POST | /auth/questionnaire/responses/ | 提交問卷回答 |
| GET/PUT | /user/profile/ | 個人資料 |
| GET/PUT | /user/soul-profile/ | 靈魂檔案 |
| GET/POST | /agent/me/ | 我的 AI 分身 |
| GET | /agent/{id}/ | 查看指定 Agent |
| GET | /agent/{id}/memories/ | Agent 記憶列表 |
| GET | /agent/{id}/reflections/ | Agent 反思列表 |
| GET/POST | /agent/{id}/intents/ | Agent 意圖管理 |
| GET | /agent/{id}/actions/ | Agent 行動佇列 |
| POST | /agent/autonomy/ | 設定自主模式 |
| GET | /match/recommendations/ | 配對推薦 |
| GET | /match/score/{user_id}/ | 配對分數詳情 |
| POST | /match/like/{user_id}/ | 標記喜歡 |
| POST | /match/connect/{user_id}/ | 請求真人連結 |
| GET | /relationship/ | 關係列表 |
| GET | /relationship/{user_id}/ | 關係詳情 |
| POST | /relationship/{user_id}/gift/ | 發送禮物 |
| GET | /chat/conversations/ | 對話列表 |
| GET | /chat/conversations/{id}/ | 對話詳情與訊息 |
| POST | /chat/start/{agent_id}/ | 開始對話 |
| POST | /chat/conversations/{id}/send/ | 發送訊息 |
| GET/POST | /chat/conversations/{id}/mode/ | 聊天模式 |
| GET | /chat/ai-reports/ | AI 報告列表 |
| GET | /chat/ai-reports/{id}/ | 報告詳情 |
| GET | /world/rooms/ | 房間列表 |
| GET | /world/room/{id}/ | 房間詳情 |
| GET | /world/room/{id}/agents/ | 房間內 Agent |
| POST | /world/agent/move/ | 移動 Agent |
| POST | /world/agent/action/ | 執行動作 |

---

## 7. 即時通訊設計

### 7.1 WebSocket 架構

```
┌────────────────────────────────────────────────────────────┐
│                  WebSocket 架構                             │
├────────────────────────────────────────────────────────────┤
│                                                            │
│   Frontend                    Backend                      │
│   ┌──────────┐               ┌──────────────────┐         │
│   │ Browser  │ ─────────────→│ ASGI Server      │         │
│   │WebSocket │               │ (Daphne)         │         │
│   └──────────┘               └────────┬─────────┘         │
│                                        │                   │
│                              ┌─────────▼─────────┐        │
│                              │ Django Channels   │        │
│                              │ Routing Layer     │        │
│                              └─────────┬─────────┘        │
│                                        │                   │
│                   ┌────────────────────┼────────────────┐ │
│                   │                    │                │ │
│           ┌───────▼───────┐   ┌───────▼───────┐        │ │
│           │ ChatConsumer  │   │ WorldConsumer │        │ │
│           │ ws/chat/{id}/ │   │ws/world/room/ │        │ │
│           └───────────────┘   └───────────────┘        │ │
│                   │                    │                │ │
│                   └────────────────────┼────────────────┘ │
│                                        │                   │
│                              ┌─────────▼─────────┐        │
│                              │ Channel Layer     │        │
│                              │ (Redis/InMemory)  │        │
│                              └───────────────────┘        │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### 7.2 ChatConsumer 事件

#### 前端 → 後端

| 事件類型 | 數據格式 | 說明 |
|---------|----------|------|
| `message` | `{content: string}` | 發送聊天訊息 |
| `typing` | `{is_typing: boolean}` | 正在輸入狀態 |
| `read` | `{message_id: string}` | 標記已讀 |

#### 後端 → 前端

| 事件類型 | 數據格式 | 說明 |
|---------|----------|------|
| `message` | `{id, content, sender_type, ...}` | 新訊息 |
| `ai_response` | `{message: {...}}` | AI 回覆 |
| `typing` | `{user_id, is_typing}` | 打字指示 |

### 7.3 WorldConsumer 事件

#### 前端 → 後端

| 事件類型 | 數據格式 | 說明 |
|---------|----------|------|
| `ping` | `{}` | 心跳檢測 |
| `move_agent` | `{agent_id, x, y}` | 移動 Agent |
| `agent_chat` | `{agent_id, message}` | 廣播聊天 |
| `agent_action` | `{agent_id, action}` | 執行動作 |
| `request_path` | `{agent_id, x, y}` | 請求 A* 路徑 |

#### 後端 → 前端

| 事件類型 | 數據格式 | 說明 |
|---------|----------|------|
| `room_state` | `{room, agents}` | 房間初始狀態 |
| `agent_position` | `{agent_id, x, y, direction}` | 位置更新 |
| `agent_path` | `{agent_id, path, speed}` | 移動路徑 |
| `agent_chat` | `{agent_id, message, duration}` | 對話氣泡 |
| `agent_action` | `{agent_id, action}` | 動作更新 |
| `agent_emotion` | `{agent_id, emotion}` | 情緒變化 |
| `agent_enter` | `{agent}` | Agent 進入房間 |
| `agent_leave` | `{agent_id}` | Agent 離開房間 |
| `pong` | `{}` | 心跳回應 |

### 7.4 群組管理

```python
# Chat 群組
chat_{conversation_id}

# World 群組
world_room_{room_id}

# 用戶通知群組
user_{user_id}
```

---

## 8. AI 系統設計

### 8.1 AI 架構概覽

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Service Layer                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│   ┌──────────────────────────────────────────────────────┐  │
│   │              LLMService (Singleton)                   │  │
│   │  ┌────────────────────────────────────────────────┐  │  │
│   │  │  Groq API (llama-3.3-70b-versatile)           │  │  │
│   │  │  - Temperature: 0.9                           │  │  │
│   │  │  - Max Tokens: 1000                          │  │  │
│   │  │  - Async Support                             │  │  │
│   │  └────────────────────────────────────────────────┘  │  │
│   └──────────────────────────────────────────────────────┘  │
│                           │                                   │
│         ┌─────────────────┼─────────────────┐               │
│         │                 │                 │               │
│    ┌────▼────┐    ┌──────▼──────┐   ┌─────▼─────┐         │
│    │  Soul   │    │   Social    │   │  Prompt   │         │
│    │  Agent  │    │   Agent     │   │  Engine   │         │
│    └─────────┘    └─────────────┘   └───────────┘         │
│                                                               │
│   ┌──────────────────────────────────────────────────────┐  │
│   │                   Service Layer                       │  │
│   │  ┌────────────┐  ┌────────────┐  ┌────────────┐     │  │
│   │  │  Memory    │  │ Reflection │  │   Intent   │     │  │
│   │  │  Service   │  │  Service   │  │  Service   │     │  │
│   │  └────────────┘  └────────────┘  └────────────┘     │  │
│   └──────────────────────────────────────────────────────┘  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 8.2 SoulAgent 對話生成流程

```
用戶訊息輸入
      ↓
┌─────────────────────────────────────┐
│  1. 收集上下文                       │
│  ├─ 靈魂檔案 (8 維度)                │
│  ├─ 相關記憶 (10 條)                 │
│  ├─ 情緒狀態                         │
│  ├─ 最近反思 (5 條)                  │
│  └─ 關係數據                         │
└─────────────────────────────────────┘
      ↓
┌─────────────────────────────────────┐
│  2. 生成說話風格                     │
│  ├─ 內外向程度                       │
│  ├─ 幽默程度                         │
│  ├─ 深度傾向                         │
│  ├─ 情感表達                         │
│  └─ MBTI 特質                        │
└─────────────────────────────────────┘
      ↓
┌─────────────────────────────────────┐
│  3. 構建 System Prompt               │
│  ├─ 身份設定                         │
│  ├─ 靈魂特質描述                     │
│  ├─ 說話風格指引                     │
│  ├─ 對話守則                         │
│  ├─ 當前狀態                         │
│  └─ 記憶與反思                       │
└─────────────────────────────────────┘
      ↓
┌─────────────────────────────────────┐
│  4. 調用 LLM                         │
│  └─ Groq API (async)                │
└─────────────────────────────────────┘
      ↓
┌─────────────────────────────────────┐
│  5. 後處理                           │
│  ├─ 儲存訊息                         │
│  ├─ 更新情緒                         │
│  ├─ 創建記憶                         │
│  └─ 廣播 WebSocket                   │
└─────────────────────────────────────┘
      ↓
AI 回覆輸出
```

### 8.3 記憶檢索演算法

**三層加權檢索 (基於 Stanford Generative Agents):**

```
Final Score = Recency × 0.4 + Importance × 0.3 + Relevance × 0.3

Recency (最近性):
- 計算時間衰減: exp(-decay_rate × hours_ago)
- 最近 1 小時內 = 1.0
- 24 小時前 ≈ 0.37

Importance (重要性):
- 直接使用 importance / 10
- 範圍: 0.1 - 1.0

Relevance (相關性):
- 向量相似度 (cosine similarity)
- 需要 embedding 模型支援
```

### 8.4 反思生成機制

```
┌─────────────────────────────────────────────┐
│           反思生成流程                       │
├─────────────────────────────────────────────┤
│                                             │
│  觸發條件:                                   │
│  ├─ 每 5 次對話後自動觸發                    │
│  └─ 每 30 分鐘定時檢查                       │
│                                             │
│  輸入:                                       │
│  └─ 最近 20 條記憶 (importance >= 4)         │
│                                             │
│  處理:                                       │
│  1. 格式化記憶文本                           │
│  2. 調用 LLM 分析 (temp=0.7)                │
│  3. 解析 JSON 結果                          │
│                                             │
│  輸出:                                       │
│  └─ 2-3 條 AgentReflection 記錄             │
│     ├─ summary: 摘要                        │
│     ├─ insight: 洞察                        │
│     └─ importance: 5-9                      │
│                                             │
│  後續影響:                                   │
│  ├─ 高重要性反思會更新情緒                   │
│  └─ 反思會注入到未來對話的 prompt            │
│                                             │
└─────────────────────────────────────────────┘
```

### 8.5 Prompt 模板結構

```
DIALOGUE_SYSTEM_PROMPT:
├── 【重要：語言設定】
├── 【你的靈魂特質】
│   ├── 三觀 (worldview, lifeview, values)
│   ├── 興趣
│   └── 性格
├── 【★ 你的說話風格指引 ★】 (動態生成)
├── 【你的戀愛特質】
├── 【對話守則】
├── 【當前關係狀態】
├── 【你現在的情緒狀態】
├── 【對話情境】 (最近 5 輪)
├── 【你對 {name} 的記憶】
└── 【你最近的反思與洞察】
```

---

## 9. 安全性設計

### 9.1 認證與授權

| 機制 | 實現方式 |
|------|----------|
| **認證** | JWT (Simple JWT) |
| **Token 有效期** | Access: 60 分鐘, Refresh: 7 天 |
| **Token 輪換** | Refresh Token 自動輪換 |
| **密碼存儲** | bcrypt 雜湊 |

### 9.2 API 安全

| 措施 | 說明 |
|------|------|
| **CORS** | 限制允許的來源域名 |
| **Rate Limiting** | LLM 呼叫限制 10 次/小時 |
| **Input Validation** | DRF Serializer 驗證 |
| **SQL Injection** | Django ORM 參數化查詢 |

### 9.3 WebSocket 安全

```python
# Token 驗證
class TokenAuthMiddleware:
    async def __call__(self, scope, receive, send):
        token = parse_token_from_query(scope)
        user = await get_user_from_token(token)
        scope['user'] = user
```

### 9.4 敏感資料保護

| 資料類型 | 保護措施 |
|---------|----------|
| 密碼 | bcrypt 雜湊，不可逆 |
| Email | 僅用於登入，不公開 |
| Soul Profile | 用戶可見，配對計算用 |
| 對話內容 | 僅對話雙方可見 |

---

## 10. 附錄

### 10.1 設定檔參考

```python
# config/settings.py 關鍵設定

# 資料庫
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        # 或 SQLite (開發)
    }
}

# JWT
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
}

# 配對權重
SOUL_MATCHING_WEIGHTS = {
    'worldview': 0.20,
    'lifeview': 0.15,
    'values': 0.20,
    'interests': 0.15,
    'personality': 0.15,
    'communication': 0.10,
    'emotional': 0.05,
}

# AI 設定
GROQ_MODEL = 'llama-3.3-70b-versatile'
MAX_LLM_CALLS_PER_HOUR = 10
LLM_COOLDOWN_SECONDS = 30
```

### 10.2 環境變數

```env
# Django
SECRET_KEY=your-secret-key
DEBUG=True
USE_SQLITE=True

# Groq
GROQ_API_KEY=gsk_xxx

# Redis
CELERY_BROKER_URL=redis://localhost:6379/1

# Database (Production)
DATABASE_URL=postgres://user:pass@host:5432/dbname
```

### 10.3 參考資料

1. **Stanford Generative Agents Paper**
   "Generative Agents: Interactive Simulacra of Human Behavior"
   https://arxiv.org/abs/2304.03442

2. **Django REST Framework**
   https://www.django-rest-framework.org/

3. **Django Channels**
   https://channels.readthedocs.io/

4. **Groq API Documentation**
   https://console.groq.com/docs

5. **Habbo Avatar API**
   https://www.habbo.com/habbo-imaging/avatarimage

---

**文件結束**

*最後更新: 2026-01-29*
*版本: 1.0*
