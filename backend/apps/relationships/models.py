"""
關係系統模型
Relationship System Models
"""

import uuid
from django.db import models
from django.conf import settings


class Relationship(models.Model):
    """
    關係 - 兩個用戶之間的關係狀態
    Relationship - Connection status between two users
    """
    STAGES = [
        ('stranger', '陌生人'),
        ('acquaintance', '認識'),
        ('friend', '朋友'),
        ('close_friend', '好友'),
        ('crush', '曖昧'),
        ('lover', '戀人'),
        ('partner', '伴侶'),
    ]

    STAGE_THRESHOLDS = {
        'stranger': 0,
        'acquaintance': 20,
        'friend': 40,
        'close_friend': 60,
        'crush': 75,
        'lover': 90,
        'partner': 100,
    }

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # 關係的兩個用戶
    user_a = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='relationships_as_a'
    )
    user_b = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='relationships_as_b'
    )

    # 關係狀態
    stage = models.CharField(max_length=20, choices=STAGES, default='stranger')
    closeness = models.IntegerField(default=0, help_text='親密度 0-100')
    trust = models.IntegerField(default=50, help_text='信任度 0-100')
    romantic = models.IntegerField(default=0, help_text='浪漫值 0-100')

    # 互動統計
    interaction_count = models.IntegerField(default=0)
    ai_interaction_count = models.IntegerField(default=0, help_text='與 AI 分身互動次數')
    real_interaction_count = models.IntegerField(default=0, help_text='真人互動次數')

    # 特殊事件
    first_met = models.DateTimeField(auto_now_add=True)
    became_friends_at = models.DateTimeField(null=True, blank=True)
    became_lovers_at = models.DateTimeField(null=True, blank=True)
    last_interaction = models.DateTimeField(auto_now=True)

    # AI 生成的關係描述
    description = models.TextField(blank=True, help_text='AI 生成的關係描述')
    shared_memories = models.JSONField(default=list, help_text='共同記憶')

    # 時間戳
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'relationships'
        verbose_name = '關係'
        verbose_name_plural = '關係'
        unique_together = ['user_a', 'user_b']
        indexes = [
            models.Index(fields=['user_a', 'stage']),
            models.Index(fields=['user_b', 'stage']),
        ]

    def __str__(self):
        return f"{self.user_a.email} ↔ {self.user_b.email}: {self.stage}"

    def update_stage(self):
        """根據親密度更新關係階段"""
        for stage, threshold in reversed(list(self.STAGE_THRESHOLDS.items())):
            if self.closeness >= threshold:
                if self.stage != stage:
                    self.stage = stage
                    self._record_stage_change(stage)
                break
        self.save()

    def _record_stage_change(self, new_stage):
        """記錄階段變化"""
        from django.utils import timezone
        if new_stage == 'friend' and not self.became_friends_at:
            self.became_friends_at = timezone.now()
        elif new_stage == 'lover' and not self.became_lovers_at:
            self.became_lovers_at = timezone.now()


class RelationshipEvent(models.Model):
    """
    關係事件 - 記錄關係中的重要事件
    Relationship Event - Records important events in the relationship
    """
    EVENT_TYPES = [
        ('first_chat', '首次對話'),
        ('stage_up', '關係升級'),
        ('gift', '送禮物'),
        ('date', '約會'),
        ('confession', '告白'),
        ('anniversary', '紀念日'),
        ('special', '特殊事件'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    relationship = models.ForeignKey(
        Relationship,
        on_delete=models.CASCADE,
        related_name='events'
    )

    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # 關聯數據
    metadata = models.JSONField(default=dict)

    # 時間戳
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'relationship_events'
        verbose_name = '關係事件'
        verbose_name_plural = '關係事件'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.relationship} - {self.event_type}: {self.title}"


class Gift(models.Model):
    """
    虛擬禮物
    Virtual Gift
    """
    GIFT_TYPES = [
        ('flower', '花束'),
        ('heart', '愛心'),
        ('star', '星星'),
        ('ring', '戒指'),
        ('teddy', '泰迪熊'),
        ('cake', '蛋糕'),
        ('music', '音樂盒'),
        ('letter', '情書'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_gifts'
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_gifts'
    )

    gift_type = models.CharField(max_length=20, choices=GIFT_TYPES)
    message = models.TextField(blank=True, max_length=500)

    # 時間戳
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'gifts'
        verbose_name = '禮物'
        verbose_name_plural = '禮物'

    def __str__(self):
        return f"{self.sender.email} → {self.receiver.email}: {self.gift_type}"
