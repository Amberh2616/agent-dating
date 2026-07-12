"""
配對系統模型
Matching System Models
"""

import uuid
from django.db import models
from django.conf import settings


class MatchScore(models.Model):
    """
    配對分數 - 兩個用戶之間的靈魂匹配度
    Match Score - Soul compatibility between two users
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # 配對的兩個用戶 (user_a.id < user_b.id 確保唯一性)
    user_a = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='match_scores_as_a'
    )
    user_b = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='match_scores_as_b'
    )

    # 總分
    total_score = models.FloatField(help_text='總匹配度 0-100')

    # 各維度分數
    worldview_score = models.FloatField(default=0, help_text='世界觀匹配度')
    lifeview_score = models.FloatField(default=0, help_text='人生觀匹配度')
    values_score = models.FloatField(default=0, help_text='價值觀匹配度')
    interests_score = models.FloatField(default=0, help_text='興趣匹配度')
    personality_score = models.FloatField(default=0, help_text='性格匹配度')
    communication_score = models.FloatField(default=0, help_text='對話風格匹配度')
    emotional_score = models.FloatField(default=0, help_text='情感需求匹配度')

    # 亮點 (最相似的點)
    highlights = models.JSONField(
        default=list,
        help_text='["都重視自由", "喜歡獨立音樂", "人生觀相近"]'
    )

    # 衝突警告
    has_dealbreaker = models.BooleanField(default=False)
    dealbreaker_reason = models.TextField(blank=True)

    # 時間戳
    calculated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'match_scores'
        verbose_name = '配對分數'
        verbose_name_plural = '配對分數'
        unique_together = ['user_a', 'user_b']
        indexes = [
            models.Index(fields=['user_a', '-total_score']),
            models.Index(fields=['user_b', '-total_score']),
        ]

    def __str__(self):
        return f"{self.user_a.email} ↔ {self.user_b.email}: {self.total_score:.1f}%"


class MatchInterest(models.Model):
    """
    配對興趣表達 - 用戶對某個配對的興趣
    Match Interest - User's interest in a match
    """
    INTEREST_STATUS = [
        ('pending', '待定'),
        ('liked', '喜歡'),
        ('passed', '跳過'),
        ('blocked', '封鎖'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='match_interests'
    )
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_interests'
    )

    status = models.CharField(max_length=20, choices=INTEREST_STATUS, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'match_interests'
        verbose_name = '配對興趣'
        verbose_name_plural = '配對興趣'
        unique_together = ['user', 'target_user']

    def __str__(self):
        return f"{self.user.email} → {self.target_user.email}: {self.status}"


class MatchRequest(models.Model):
    """
    真人連結請求 - 請求與某人的真人對話
    Match Request - Request for real person connection
    """
    REQUEST_STATUS = [
        ('pending', '等待中'),
        ('accepted', '已接受'),
        ('rejected', '已拒絕'),
        ('expired', '已過期'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_match_requests'
    )
    target = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_match_requests'
    )

    # 狀態
    status = models.CharField(max_length=20, choices=REQUEST_STATUS, default='pending')
    message = models.TextField(blank=True, help_text='請求訊息')

    # 時間戳
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'match_requests'
        verbose_name = '真人連結請求'
        verbose_name_plural = '真人連結請求'

    def __str__(self):
        return f"{self.requester.email} → {self.target.email}: {self.status}"
