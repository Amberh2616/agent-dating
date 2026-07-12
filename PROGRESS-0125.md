# 進度記錄 - 2026-01-25

## 今日目標
1. ~~讓 AI 分身在虛擬世界中自主移動、社交、對話~~
2. **實現三模式聊天系統** ✅ DONE

---

## 新完成 - 三模式聊天系統 (下午)

### 實現的功能

#### 1. 資料模型
- `Conversation.mode` 欄位 (ai/user/paused)
- `Conversation.mode_changed_at` 時間戳
- `ConversationSummary` 模型 (印象分、話題、亮點等)

#### 2. AI 任務
- `generate_agent_response()` 添加模式檢查
- `generate_conversation_summary()` AI 生成對話報告
- `trigger_scheduled_ai_conversations()` 定時觸發 AI 對話

#### 3. API 端點
- `GET/POST /api/chat/conversations/:id/mode/` - 模式切換
- `GET /api/chat/conversations/:id/impression/` - 印象分歷史
- `GET /api/chat/ai-reports/` - AI 報告列表
- `GET /api/chat/ai-reports/:id/` - 報告詳情

#### 4. 前端 UI
- AI 報告面板 (右上角，含未讀計數)
- 聊天框模式切換按鈕 (AI 代聊 / 我來聊)
- 模式指示器

#### 5. 定時任務
- APScheduler 每小時觸發 AI 對話
- 選擇高配對分 (>60%) 且 6 小時未聊的配對

### 使用流程
```
1. 用戶登入 → 看到 AI 報告面板
2. AI 自動幫用戶和配對對象聊天
3. 用戶看報告了解進展
4. 用戶可以切換到「我來聊」模式接手
```

---

## 早上已完成 (成功)

### 1. AI-to-AI 對話系統
- 使用 Groq LLM (llama-3.3-70b-versatile) 生成 AI 對話
- Agent model 新增 `last_chat_message` 和 `last_chat_time` 欄位
- API 返回最近 30 秒內的對話訊息
- 對話成功存入資料庫

### 2. Agent 移動模擬
- APScheduler 定時任務 (每 5 秒)
- Agent 在房間內隨機移動
- 位置更新存入 AgentPosition model
- 前端 polling 每 3 秒獲取位置更新
- **移動動畫正常顯示**

### 3. 前端 Polling 系統
- 每 3 秒從 `/api/world/room/{id}/agents/` 獲取 agent 狀態
- 成功獲取 agent 位置和聊天訊息
- 位置動畫 (animateAgentPath) 運作正常

### 4. 測試頁面
- `test-bubble.html` 氣泡顯示 **正常運作**
- 獨立測試證明氣泡代碼本身沒問題

---

## 失敗的部分

### 前端對話氣泡顯示 - 完全失敗

**問題描述:**
在 `index.html` 主頁面中，無法顯示任何動態創建的 DOM 元素。

**嘗試過的方法 (全部失敗):**

1. **Phaser DOM Element** (`gameScene.add.dom()`)
   - 結果: 無顯示

2. **Phaser Graphics + Text**
   - 結果: 閃 2 秒後消失，不穩定

3. **HTML Overlay (document.createElement)**
   - 結果: 完全無顯示

4. **Fixed Position Bubble (z-index: 99999)**
   - 結果: 無顯示

5. **Pre-created Hidden Element (display: none -> block)**
   - 結果: 無顯示

6. **Bubble Inside Debug Panel**
   - 結果: 無顯示

7. **Modify Debug Panel Background Color**
   - 結果: 待測試

**奇怪的現象:**
- `test-bubble.html` 完全正常
- `index.html` Debug Panel 的文字可以看到
- 但任何新增或修改的元素都看不到

**可能原因推測:**
1. Phaser canvas 覆蓋整個頁面，吃掉了事件或渲染
2. CSS `overflow: hidden` 影響
3. 瀏覽器快取問題
4. JavaScript 執行順序問題
5. 某個未知的 CSS 規則隱藏了元素

---

## 技術細節

### 後端 API 返回格式
```json
{
  "agents": [
    {
      "id": "uuid",
      "name": "Amber",
      "x": 5,
      "y": 3,
      "direction": 2,
      "action": "idle",
      "emotion": "neutral",
      "is_online": true,
      "chat_message": "Hello!"  // 30秒內的訊息
    }
  ]
}
```

### 前端 Polling 代碼位置
`frontend/index.html` - `pollAgentPositions()` 函數

### 後端相關檔案
- `backend/apps/agents/models.py` - Agent model
- `backend/apps/world/views.py` - RoomAgentsView API
- `backend/apps/agents/management/commands/run_agent_scheduler.py` - 模擬器

---

## 下一步建議

1. **徹底檢查 index.html 的 CSS**
   - 檢查是否有全局規則影響 fixed 元素

2. **重寫前端架構**
   - 考慮不用 Phaser，改用純 HTML/CSS
   - 或將 UI 層完全分離

3. **使用瀏覽器開發者工具**
   - 檢查 Elements 面板，確認元素是否被創建
   - 檢查 Computed Styles，看是否被隱藏

4. **測試其他瀏覽器**
   - Chrome / Firefox / Edge

---

## 運行中的服務

```bash
# Backend
cd agent-dating/backend
python manage.py runserver  # Port 8000

# Frontend
cd agent-dating/frontend
npx serve -p 3000  # Port 3000

# Agent Scheduler (背景)
python manage.py run_agent_scheduler --interval 5 --sync
```

---

## 測試帳號

| Email | Password | Agent |
|-------|----------|-------|
| amberh2616@gmail.com | 1234 | Amber |
| maria@test.com | 1234 | Mike |
