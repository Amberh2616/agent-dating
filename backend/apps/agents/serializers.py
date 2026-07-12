"""
AI 分身序列化器
Agent Serializers
"""

from rest_framework import serializers
from .models import Agent, Memory, DailyPlan, AgentAction


class AgentSerializer(serializers.ModelSerializer):
    """AI 分身序列化器"""
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Agent
        fields = [
            'id', 'user_email', 'name', 'avatar_look', 'bio',
            'current_location', 'current_action', 'current_emotion',
            'is_online', 'is_autonomous',
            'total_conversations', 'total_friends_made',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user_email', 'current_location', 'current_action',
            'current_emotion', 'is_online', 'total_conversations',
            'total_friends_made', 'created_at', 'updated_at'
        ]


class AgentCreateSerializer(serializers.ModelSerializer):
    """AI 分身創建序列化器"""

    class Meta:
        model = Agent
        fields = ['name', 'avatar_look', 'bio']


class MemorySerializer(serializers.ModelSerializer):
    """記憶序列化器"""

    class Meta:
        model = Memory
        fields = [
            'id', 'type', 'content', 'importance',
            'related_agents', 'location', 'emotion',
            'last_accessed', 'access_count', 'created_at'
        ]
        read_only_fields = ['id', 'last_accessed', 'access_count', 'created_at']


class DailyPlanSerializer(serializers.ModelSerializer):
    """每日計畫序列化器"""

    class Meta:
        model = DailyPlan
        fields = ['id', 'date', 'schedule', 'current_hour_index', 'is_completed', 'created_at']
        read_only_fields = ['id', 'created_at']


class AgentActionSerializer(serializers.ModelSerializer):
    """行動序列化器"""

    class Meta:
        model = AgentAction
        fields = [
            'id', 'action_type', 'target_location', 'target_agent',
            'parameters', 'priority', 'status',
            'created_at', 'started_at', 'completed_at'
        ]
        read_only_fields = ['id', 'created_at', 'started_at', 'completed_at']


class AgentPublicSerializer(serializers.ModelSerializer):
    """AI 分身公開資訊 (給其他用戶看)"""

    class Meta:
        model = Agent
        fields = [
            'id', 'name', 'avatar_look', 'bio',
            'current_emotion', 'is_online'
        ]
