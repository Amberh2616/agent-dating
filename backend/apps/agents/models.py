"""
AI 分身模型
AI Agent Models - Represents user's soul in the virtual world
"""

import uuid
from django.db import models
from django.conf import settings


class Agent(models.Model):
    """
    AI 分身 - 用戶在虛擬世界的代表
    AI Agent - User's representation in the virtual world
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='agent'
    )

    # 基本資訊
    name = models.CharField(max_length=100, help_text='AI 分身名稱')
    avatar_look = models.CharField(
        max_length=500,
        blank=True,
        help_text='Habbo look code (e.g., hd-180-1.hr-100-61.ch-210-66)'
    )
    bio = models.TextField(blank=True, max_length=500, help_text='AI 分身自我介紹')

    # 當前狀態
    current_location = models.JSONField(
        default=dict,
        help_text='{"x": 0, "y": 0, "z": 0, "room_id": "uuid"}'
    )
    current_action = models.CharField(
        max_length=50,
        default='idle',
        help_text='idle | walking | talking | sitting | dancing'
    )
    current_emotion = models.CharField(
        max_length=50,
        default='neutral',
        help_text='neutral | happy | sad | excited | thinking'
    )

    # 情緒動態系統 (0-100)
    emotion_state = models.JSONField(
        default=dict,
        help_text='''{
            "happiness": 50,    # 0=難過 ↔ 100=開心
            "energy": 50,       # 0=疲憊 ↔ 100=有活力
            "stress": 30,       # 0=平靜 ↔ 100=緊張
            "openness": 50      # 0=封閉 ↔ 100=開放
        }'''
    )
    emotion_baseline = models.JSONField(
        default=dict,
        help_text='情緒基準線，根據性格設定，情緒會慢慢回歸這個值'
    )

    current_target = models.UUIDField(
        null=True,
        blank=True,
        help_text='目前互動對象的 Agent ID'
    )

    # 最近的聊天訊息（用於前端顯示氣泡）
    last_chat_message = models.CharField(
        max_length=200,
        blank=True,
        default='',
        help_text='最近說的話'
    )
    last_chat_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text='最近說話時間'
    )

    # 線上狀態
    is_online = models.BooleanField(default=False)
    is_autonomous = models.BooleanField(
        default=True,
        help_text='是否自主行動（用戶可以接管）'
    )
    last_active = models.DateTimeField(auto_now=True)

    # 統計資料
    total_conversations = models.IntegerField(default=0)
    total_friends_made = models.IntegerField(default=0)

    # 時間戳
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'agents'
        verbose_name = 'AI 分身'
        verbose_name_plural = 'AI 分身'

    def __str__(self):
        return f"{self.name} ({self.user.email})"

    def get_emotion_state(self) -> dict:
        """獲取當前情緒狀態，確保有預設值"""
        default = {
            'happiness': 50,
            'energy': 50,
            'stress': 30,
            'openness': 50
        }
        if not self.emotion_state:
            return default
        return {**default, **self.emotion_state}

    def get_emotion_baseline(self) -> dict:
        """獲取情緒基準線，根據性格設定"""
        default = {
            'happiness': 50,
            'energy': 50,
            'stress': 30,
            'openness': 50
        }
        if not self.emotion_baseline:
            # 嘗試從性格計算基準線
            try:
                personality = self.user.soul_profile.personality or {}
                traits = personality.get('traits', {})
                introversion = traits.get('introversion', 50)
                # 外向者基準 energy 較高
                default['energy'] = 70 - int(introversion * 0.4)
                # 外向者基準 openness 較高
                default['openness'] = 70 - int(introversion * 0.4)
            except Exception:
                pass
            return default
        return {**default, **self.emotion_baseline}

    def update_emotion(self, changes: dict, decay_rate: float = 0.1):
        """
        更新情緒狀態

        Args:
            changes: {"happiness": +10, "stress": -5}
            decay_rate: 情緒回歸基準線的速率 (0-1)
        """
        current = self.get_emotion_state()
        baseline = self.get_emotion_baseline()

        for key, delta in changes.items():
            if key in current:
                # 應用變化
                current[key] = max(0, min(100, current[key] + delta))

        # 情緒緩慢回歸基準線
        for key in current:
            diff = baseline.get(key, 50) - current[key]
            current[key] = current[key] + int(diff * decay_rate)

        self.emotion_state = current

        # 更新 current_emotion (舊的字串格式，向後兼容)
        self.current_emotion = self._derive_emotion_label()
        self.save(update_fields=['emotion_state', 'current_emotion'])

    def _derive_emotion_label(self) -> str:
        """從情緒數值推導出情緒標籤"""
        state = self.get_emotion_state()
        happiness = state.get('happiness', 50)
        energy = state.get('energy', 50)
        stress = state.get('stress', 30)

        if stress > 70:
            return 'stressed'
        elif happiness > 70 and energy > 60:
            return 'excited'
        elif happiness > 60:
            return 'happy'
        elif happiness < 30:
            return 'sad'
        elif energy < 30:
            return 'tired'
        elif state.get('openness', 50) < 30:
            return 'thinking'
        else:
            return 'neutral'

    def get_emotion_description(self) -> str:
        """獲取情緒的文字描述，用於 AI prompt"""
        state = self.get_emotion_state()
        parts = []

        happiness = state.get('happiness', 50)
        if happiness > 70:
            parts.append("心情很好")
        elif happiness > 55:
            parts.append("心情不錯")
        elif happiness < 30:
            parts.append("有點低落")
        elif happiness < 45:
            parts.append("心情一般")

        energy = state.get('energy', 50)
        if energy > 70:
            parts.append("精力充沛")
        elif energy < 30:
            parts.append("有點疲憊")

        stress = state.get('stress', 30)
        if stress > 70:
            parts.append("感到緊張")
        elif stress > 50:
            parts.append("有些壓力")
        elif stress < 20:
            parts.append("很放鬆")

        openness = state.get('openness', 50)
        if openness > 70:
            parts.append("很願意交流")
        elif openness < 30:
            parts.append("想安靜一下")

        return "、".join(parts) if parts else "情緒平穩"


class Memory(models.Model):
    """
    記憶流 - AI 分身的記憶系統
    Memory Stream - Agent's memory system (inspired by Stanford Generative Agents)
    """
    MEMORY_TYPES = [
        ('observation', '觀察'),      # 感知到的事件
        ('reflection', '反思'),       # 高層次洞察
        ('plan', '計畫'),            # 未來行動計畫
        ('conversation', '對話'),     # 對話記錄
        ('emotion', '情感'),          # 情感記錄
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='memories')

    # 記憶內容
    type = models.CharField(max_length=20, choices=MEMORY_TYPES)
    content = models.TextField(help_text='記憶內容描述')
    importance = models.IntegerField(
        default=5,
        help_text='重要性評分 1-10'
    )

    # 關聯資料
    related_agents = models.JSONField(
        default=list,
        help_text='相關 Agent IDs'
    )
    location = models.JSONField(
        default=dict,
        help_text='發生地點 {"x": 0, "y": 0, "room_id": "uuid"}'
    )
    emotion = models.CharField(
        max_length=50,
        blank=True,
        help_text='當時的情感狀態'
    )

    # 向量嵌入 (用於語意檢索)
    embedding = models.JSONField(
        default=list,
        help_text='Memory embedding vector (1536 dimensions)'
    )

    # 檢索相關
    last_accessed = models.DateTimeField(auto_now=True)
    access_count = models.IntegerField(default=0)

    # 時間戳
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'memories'
        verbose_name = '記憶'
        verbose_name_plural = '記憶'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['agent', 'type']),
            models.Index(fields=['agent', 'importance']),
            models.Index(fields=['agent', '-created_at']),
        ]

    def __str__(self):
        return f"{self.agent.name} - {self.type}: {self.content[:50]}..."


class DailyPlan(models.Model):
    """
    每日計畫 - AI 分身的日程安排
    Daily Plan - Agent's daily schedule
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='daily_plans')

    # 計畫內容
    date = models.DateField()
    schedule = models.JSONField(
        default=list,
        help_text='''
        [
            {"hour": 8, "activity": "起床", "location": "bedroom"},
            {"hour": 9, "activity": "在咖啡廳閒逛", "location": "cafe"},
            {"hour": 12, "activity": "和朋友聊天", "location": "plaza"},
            ...
        ]
        '''
    )

    # 執行狀態
    current_hour_index = models.IntegerField(default=0)
    is_completed = models.BooleanField(default=False)

    # 時間戳
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'daily_plans'
        verbose_name = '每日計畫'
        verbose_name_plural = '每日計畫'
        unique_together = ['agent', 'date']

    def __str__(self):
        return f"{self.agent.name} - {self.date}"


class AgentAction(models.Model):
    """
    行動佇列 - AI 分身待執行的行動
    Action Queue - Pending actions for the agent
    """
    ACTION_TYPES = [
        ('move', '移動'),
        ('chat', '對話'),
        ('wave', '打招呼'),
        ('sit', '坐下'),
        ('stand', '站起'),
        ('dance', '跳舞'),
        ('think', '思考'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='actions')

    # 行動內容
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    target_location = models.JSONField(
        null=True,
        blank=True,
        help_text='目標位置 {"x": 0, "y": 0}'
    )
    target_agent = models.ForeignKey(
        Agent,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='targeted_by_actions'
    )
    parameters = models.JSONField(
        default=dict,
        help_text='行動參數'
    )

    # 執行狀態
    priority = models.IntegerField(default=5, help_text='優先級 1-10')
    status = models.CharField(
        max_length=20,
        default='pending',
        help_text='pending | executing | completed | cancelled'
    )

    # 時間戳
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'agent_actions'
        verbose_name = '行動'
        verbose_name_plural = '行動'
        ordering = ['-priority', 'created_at']

    def __str__(self):
        return f"{self.agent.name} - {self.action_type}"


class AgentReflection(models.Model):
    """
    反思/洞察 - 從多條記憶生成的高級理解
    Reflection - Higher-level understanding from multiple memories
    (Inspired by Stanford Generative Agents)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='reflections')

    # 反思內容
    summary = models.TextField(help_text='摘要 "X和我聊了音樂"')
    insight = models.TextField(help_text='洞察 "她今晚想去咖啡廳"')
    based_on_memories = models.ManyToManyField(Memory, blank=True, related_name='derived_reflections')

    # 重要性
    importance = models.IntegerField(default=5, help_text='重要性 1-10')

    # 時間戳
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'agent_reflections'
        verbose_name = '反思'
        verbose_name_plural = '反思'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['agent', '-created_at']),
            models.Index(fields=['agent', 'importance']),
        ]

    def __str__(self):
        return f"{self.agent.name}: {self.summary[:50]}..."


class AgentIntent(models.Model):
    """
    意圖/目標 - 短期計劃
    Intent - Short-term goals and plans
    """
    INTENT_STATUS = [
        ('pending', '待執行'),
        ('active', '執行中'),
        ('completed', '已完成'),
        ('expired', '已過期'),
        ('cancelled', '已取消'),
    ]
    GOAL_TYPES = [
        ('make_friend', '認識新朋友'),
        ('chat_topic', '聊特定話題'),
        ('explore_room', '探索房間'),
        ('follow_up', '跟進舊友'),
        ('rest', '休息'),
        ('observe', '觀察'),
        ('socialize', '社交'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='intents')

    # 目標
    goal = models.CharField(max_length=200, help_text='目標描述 "認識2個新朋友"')
    goal_type = models.CharField(max_length=30, choices=GOAL_TYPES)
    target_agent = models.ForeignKey(
        Agent,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='targeted_by_intents'
    )
    target_topic = models.CharField(max_length=100, blank=True, help_text='目標話題 "旅行"')

    # 執行狀態
    status = models.CharField(max_length=20, choices=INTENT_STATUS, default='pending')
    priority = models.IntegerField(default=5, help_text='優先級 1-10')

    # 步驟分解
    steps = models.JSONField(
        default=list,
        help_text='["找對象", "打招呼", "交換興趣"]'
    )
    current_step = models.IntegerField(default=0)

    # 進度追蹤
    progress_notes = models.JSONField(default=list, help_text='執行過程記錄')

    # 過期時間
    expires_at = models.DateTimeField()

    # 時間戳
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'agent_intents'
        verbose_name = '意圖'
        verbose_name_plural = '意圖'
        ordering = ['-priority', 'created_at']
        indexes = [
            models.Index(fields=['agent', 'status']),
            models.Index(fields=['agent', '-priority']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"{self.agent.name}: {self.goal} ({self.status})"

    @property
    def current_step_name(self):
        """獲取當前步驟名稱"""
        if self.steps and 0 <= self.current_step < len(self.steps):
            return self.steps[self.current_step]
        return None

    @property
    def is_expired(self):
        """檢查是否過期"""
        from django.utils import timezone
        return timezone.now() > self.expires_at


class InteractionLog(models.Model):
    """
    交互日誌 - 事件匯流排
    Interaction Log - Event bus for all agent interactions
    """
    EVENT_TYPES = [
        ('agent_enter', '進入房間'),
        ('agent_exit', '離開房間'),
        ('chat_message', '聊天'),
        ('proximity', '靠近'),
        ('invite', '邀請'),
        ('wave', '打招呼'),
        ('gift', '送禮'),
        ('emotion_detect', '情緒偵測'),
        ('goal_achieved', '達成目標'),
        ('intent_start', '開始意圖'),
        ('intent_complete', '完成意圖'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(
        'world.Room',
        on_delete=models.CASCADE,
        related_name='interaction_logs'
    )
    agent = models.ForeignKey(
        Agent,
        on_delete=models.CASCADE,
        related_name='interactions_as_actor'
    )
    target_agent = models.ForeignKey(
        Agent,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='interactions_as_target'
    )

    # 事件類型
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES)

    # 事件資料
    payload = models.JSONField(default=dict, help_text='事件附加資料')

    # 位置
    location_x = models.IntegerField(null=True, blank=True)
    location_y = models.IntegerField(null=True, blank=True)

    # 時間戳
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'interaction_logs'
        verbose_name = '交互日誌'
        verbose_name_plural = '交互日誌'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['room', '-created_at']),
            models.Index(fields=['agent', '-created_at']),
            models.Index(fields=['event_type', '-created_at']),
        ]

    def __str__(self):
        target_str = f" → {self.target_agent.name}" if self.target_agent else ""
        return f"{self.agent.name}{target_str}: {self.event_type}"
