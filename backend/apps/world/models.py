"""
虛擬世界模型
Virtual World Models - Habbo-style rooms and locations
"""

import uuid
from django.db import models
from django.conf import settings


class Room(models.Model):
    """
    房間 - 虛擬世界中的空間
    Room - Spaces in the virtual world
    """
    ROOM_TYPES = [
        ('public', '公共區域'),
        ('cafe', '咖啡廳'),
        ('plaza', '廣場'),
        ('park', '公園'),
        ('bar', '酒吧'),
        ('library', '圖書館'),
        ('gym', '健身房'),
        ('private', '私人房間'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES, default='public')

    # 房間主人 (私人房間)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_rooms'
    )

    # 房間配置
    width = models.IntegerField(default=20)
    height = models.IntegerField(default=20)
    floor_plan = models.JSONField(
        default=list,
        help_text='2D array of walkable tiles'
    )
    spawn_points = models.JSONField(
        default=list,
        help_text='[{"x": 5, "y": 5}, ...]'
    )

    # 房間裝飾/家具 (Habbo 風格)
    furniture = models.JSONField(
        default=list,
        help_text='''
        [
            {"type": "sofa", "x": 3, "y": 4, "rotation": 2},
            {"type": "table", "x": 5, "y": 5, "rotation": 0},
            ...
        ]
        '''
    )

    # 容量與狀態
    max_capacity = models.IntegerField(default=50)
    is_active = models.BooleanField(default=True)
    is_visible = models.BooleanField(default=True)

    # 統計
    visit_count = models.IntegerField(default=0)

    # 時間戳
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'rooms'
        verbose_name = '房間'
        verbose_name_plural = '房間'

    def __str__(self):
        return f"{self.name} ({self.room_type})"


class AgentPosition(models.Model):
    """
    Agent 位置 - AI 分身在房間中的即時位置
    Agent Position - Real-time position of AI agents in rooms
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.OneToOneField(
        'agents.Agent',
        on_delete=models.CASCADE,
        related_name='position'
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='agent_positions'
    )

    # 位置
    x = models.IntegerField(default=0)
    y = models.IntegerField(default=0)
    z = models.IntegerField(default=0, help_text='樓層/高度')
    direction = models.IntegerField(default=2, help_text='面向方向 0-7')

    # 狀態
    is_sitting = models.BooleanField(default=False)
    is_moving = models.BooleanField(default=False)
    target_x = models.IntegerField(null=True, blank=True)
    target_y = models.IntegerField(null=True, blank=True)

    # 時間戳
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'agent_positions'
        verbose_name = 'Agent 位置'
        verbose_name_plural = 'Agent 位置'

    def __str__(self):
        return f"{self.agent.name} at ({self.x}, {self.y}) in {self.room}"


class WorldEvent(models.Model):
    """
    世界事件 - 虛擬世界中發生的事件
    World Event - Events happening in the virtual world
    """
    EVENT_TYPES = [
        ('agent_enter', 'Agent 進入房間'),
        ('agent_leave', 'Agent 離開房間'),
        ('agent_chat', 'Agent 對話'),
        ('agent_action', 'Agent 動作'),
        ('room_announcement', '房間公告'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='events')
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES)

    # 事件主體
    agent = models.ForeignKey(
        'agents.Agent',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='world_events'
    )
    target_agent = models.ForeignKey(
        'agents.Agent',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='targeted_world_events'
    )

    # 事件內容
    content = models.TextField(blank=True)
    metadata = models.JSONField(default=dict)

    # 位置
    x = models.IntegerField(null=True, blank=True)
    y = models.IntegerField(null=True, blank=True)

    # 時間戳
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'world_events'
        verbose_name = '世界事件'
        verbose_name_plural = '世界事件'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['room', '-created_at']),
        ]

    def __str__(self):
        return f"{self.room.name} - {self.event_type}"
