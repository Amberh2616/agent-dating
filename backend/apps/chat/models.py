"""
聊天系統模型
Chat System Models
"""

import uuid
from django.db import models
from django.conf import settings


class Conversation(models.Model):
    """
    對話 - 用戶與 AI 分身或真人的對話
    Conversation - Chat between user and AI agent or real person
    """
    CONVERSATION_TYPES = [
        ('user_to_agent', '用戶對AI'),     # 用戶和別人的 AI 聊天
        ('agent_to_agent', 'AI對AI'),      # 兩個 AI 分身的自動對話
        ('user_to_user', '真人對話'),       # 配對成功後的真人對話
    ]

    CHAT_MODES = [
        ('ai', 'AI 代聊'),
        ('user', '用戶親自'),
        ('paused', '暫停'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    conversation_type = models.CharField(max_length=20, choices=CONVERSATION_TYPES)

    # 聊天模式 - AI 代聊 / 用戶親自 / 暫停
    mode = models.CharField(max_length=10, choices=CHAT_MODES, default='ai')
    mode_changed_at = models.DateTimeField(null=True, blank=True)

    # 參與者 - 用戶 (可選)
    user_participant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='conversations_as_user'
    )

    # 參與者 - AI 分身 (可選)
    agent_participant = models.ForeignKey(
        'agents.Agent',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='conversations_as_participant'
    )

    # 對方 - 可以是 AI 或用戶
    other_agent = models.ForeignKey(
        'agents.Agent',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='conversations_as_other'
    )
    other_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='conversations_as_other_user'
    )

    # 對話狀態
    is_active = models.BooleanField(default=True)
    is_archived = models.BooleanField(default=False)
    unread_count = models.IntegerField(default=0)

    # 統計
    message_count = models.IntegerField(default=0)
    last_message_preview = models.CharField(max_length=200, blank=True)
    last_message_at = models.DateTimeField(null=True, blank=True)

    # 時間戳
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'conversations'
        verbose_name = '對話'
        verbose_name_plural = '對話'
        ordering = ['-last_message_at']

    def __str__(self):
        return f"Conversation {self.id} ({self.conversation_type})"


class Message(models.Model):
    """
    訊息 - 對話中的單條訊息
    Message - Single message in a conversation
    """
    SENDER_TYPES = [
        ('user', '用戶'),
        ('agent', 'AI 分身'),
    ]

    MESSAGE_TYPES = [
        ('text', '文字'),
        ('image', '圖片'),
        ('gift', '禮物'),
        ('system', '系統通知'),
        ('action', '動作'),  # e.g., "小明 送了一束花"
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )

    # 發送者
    sender_type = models.CharField(max_length=10, choices=SENDER_TYPES)
    sender_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_messages'
    )
    sender_agent = models.ForeignKey(
        'agents.Agent',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_messages'
    )

    # 訊息內容
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default='text')
    content = models.TextField()
    metadata = models.JSONField(default=dict, help_text='附加資料 (圖片URL, 禮物類型等)')

    # AI 生成相關
    emotion = models.CharField(max_length=50, blank=True, help_text='訊息帶有的情感')
    is_ai_generated = models.BooleanField(default=False)

    # 狀態
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    # 時間戳
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'messages'
        verbose_name = '訊息'
        verbose_name_plural = '訊息'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
            models.Index(fields=['sender_user', '-created_at']),
        ]

    def __str__(self):
        sender = self.sender_user or self.sender_agent
        return f"{sender}: {self.content[:50]}..."

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # 更新對話的最後訊息
        self.conversation.last_message_preview = self.content[:200]
        self.conversation.last_message_at = self.created_at
        self.conversation.message_count = self.conversation.messages.count()
        self.conversation.save(update_fields=['last_message_preview', 'last_message_at', 'message_count'])


class ChatContext(models.Model):
    """
    對話上下文 - AI 對話時的記憶上下文
    Chat Context - Memory context for AI conversations
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.OneToOneField(
        Conversation,
        on_delete=models.CASCADE,
        related_name='context'
    )

    # 摘要 (定期由 AI 生成)
    summary = models.TextField(blank=True, help_text='對話摘要')
    key_topics = models.JSONField(default=list, help_text='關鍵話題')
    shared_interests = models.JSONField(default=list, help_text='發現的共同興趣')
    emotional_trajectory = models.JSONField(default=list, help_text='情感變化軌跡')

    # 上下文窗口 (最近的訊息用於 LLM 提示)
    recent_messages_json = models.JSONField(default=list, help_text='最近 20 條訊息')

    # 時間戳
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'chat_contexts'
        verbose_name = '對話上下文'
        verbose_name_plural = '對話上下文'

    def __str__(self):
        return f"Context for {self.conversation_id}"


class ConversationSummary(models.Model):
    """
    對話摘要 - AI 代聊後生成的報告
    Conversation Summary - Report generated after AI conversations
    """
    COMPATIBILITY_TRENDS = [
        ('up', '上升'),
        ('down', '下降'),
        ('neutral', '持平'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='summaries'
    )

    # 時間範圍
    period_start = models.DateTimeField(help_text='摘要涵蓋的開始時間')
    period_end = models.DateTimeField(help_text='摘要涵蓋的結束時間')
    message_count = models.IntegerField(default=0, help_text='此期間的訊息數')

    # AI 生成的內容
    summary_text = models.TextField(help_text='AI 生成的對話摘要')
    key_topics = models.JSONField(default=list, help_text='關鍵話題列表')
    emotional_tone = models.CharField(max_length=50, blank=True, help_text='情感基調')
    best_moment = models.TextField(blank=True, help_text='最佳時刻/亮點')
    shared_interests_found = models.JSONField(default=list, help_text='發現的共同興趣')

    # 印象分數
    impression_score = models.IntegerField(
        default=50,
        help_text='當前印象分 (0-100)'
    )
    impression_delta = models.IntegerField(
        default=0,
        help_text='印象分變化 (-10 to +10)'
    )
    compatibility_trend = models.CharField(
        max_length=20,
        choices=COMPATIBILITY_TRENDS,
        default='neutral',
        help_text='配對趨勢'
    )

    # 狀態
    is_read = models.BooleanField(default=False, help_text='用戶是否已讀')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'conversation_summaries'
        verbose_name = '對話摘要'
        verbose_name_plural = '對話摘要'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['conversation', '-created_at']),
            models.Index(fields=['is_read', '-created_at']),
        ]

    def __str__(self):
        return f"Summary for {self.conversation_id} ({self.period_start.date()})"
