"""
AI 分身視圖
Agent Views

Includes Generative Agents endpoints for:
- Memories
- Reflections
- Intents
- Actions
"""

from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Agent, Memory, AgentReflection, AgentIntent, InteractionLog
from .serializers import (
    AgentSerializer,
    AgentCreateSerializer,
    MemorySerializer,
    AgentPublicSerializer,
)
from .services.memory_service import memory_service
from .services.reflection_service import reflection_service
from .services.intent_service import intent_service


class MyAgentView(APIView):
    """我的 AI 分身"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """獲取我的 AI 分身"""
        try:
            agent = request.user.agent
            serializer = AgentSerializer(agent)
            return Response(serializer.data)
        except Agent.DoesNotExist:
            return Response(
                {"message": "尚未創建 AI 分身"},
                status=status.HTTP_404_NOT_FOUND
            )

    def post(self, request):
        """創建我的 AI 分身"""
        if hasattr(request.user, 'agent'):
            return Response(
                {"message": "已有 AI 分身"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = AgentCreateSerializer(data=request.data)
        if serializer.is_valid():
            agent = serializer.save(user=request.user)
            return Response(
                AgentSerializer(agent).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        """更新我的 AI 分身"""
        try:
            agent = request.user.agent
        except Agent.DoesNotExist:
            return Response(
                {"message": "尚未創建 AI 分身"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = AgentSerializer(agent, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AgentDetailView(APIView):
    """查看指定 AI 分身"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, agent_id):
        """獲取指定 AI 分身的公開資訊"""
        agent = get_object_or_404(Agent, id=agent_id)
        serializer = AgentPublicSerializer(agent)
        return Response(serializer.data)


class AgentMemoriesView(APIView):
    """AI 分身的記憶"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, agent_id):
        """獲取 AI 分身的記憶 (僅限自己的 AI)"""
        agent = get_object_or_404(Agent, id=agent_id)

        # 只能查看自己的 AI 記憶
        if agent.user != request.user:
            return Response(
                {"message": "無權查看"},
                status=status.HTTP_403_FORBIDDEN
            )

        memory_type = request.query_params.get('type')
        limit = int(request.query_params.get('limit', 50))

        memories = Memory.objects.filter(agent=agent)
        if memory_type:
            memories = memories.filter(type=memory_type)

        memories = memories.order_by('-created_at')[:limit]
        serializer = MemorySerializer(memories, many=True)
        return Response(serializer.data)


class AgentAutonomyView(APIView):
    """切換 AI 自主模式"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """切換自主/手動控制模式"""
        try:
            agent = request.user.agent
        except Agent.DoesNotExist:
            return Response(
                {"message": "尚未創建 AI 分身"},
                status=status.HTTP_404_NOT_FOUND
            )

        is_autonomous = request.data.get('is_autonomous', True)
        agent.is_autonomous = is_autonomous
        agent.save()

        return Response({
            "message": f"已切換為{'自主模式' if is_autonomous else '手動控制模式'}",
            "is_autonomous": agent.is_autonomous
        })


# === Generative Agents Endpoints ===

class AgentReflectionsView(APIView):
    """AI 分身的反思/洞察"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, agent_id):
        """
        獲取 AI 分身的反思列表
        GET /api/agent/<agent_id>/reflections/
        Query params:
            - limit: 最大數量 (default: 10)
            - min_importance: 最低重要性 (default: 0)
        """
        agent = get_object_or_404(Agent, id=agent_id)

        # 只能查看自己的 AI 反思
        if agent.user != request.user:
            return Response(
                {"message": "無權查看"},
                status=status.HTTP_403_FORBIDDEN
            )

        limit = int(request.query_params.get('limit', 10))
        min_importance = int(request.query_params.get('min_importance', 0))

        reflections = reflection_service.get_reflections(
            str(agent_id),
            limit=limit,
            min_importance=min_importance
        )

        return Response({
            "count": len(reflections),
            "reflections": reflections
        })

    def post(self, request, agent_id):
        """
        手動觸發反思生成
        POST /api/agent/<agent_id>/reflections/
        """
        agent = get_object_or_404(Agent, id=agent_id)

        if agent.user != request.user:
            return Response(
                {"message": "無權操作"},
                status=status.HTTP_403_FORBIDDEN
            )

        # 獲取語言偏好
        language = request.user.preferred_language or 'zh-hant'

        # 生成反思
        new_reflections = reflection_service.generate_reflection(
            str(agent_id),
            language=language
        )

        return Response({
            "message": f"生成了 {len(new_reflections)} 條反思",
            "reflections": [
                {
                    'id': str(r.id),
                    'summary': r.summary,
                    'insight': r.insight,
                    'importance': r.importance,
                    'created_at': r.created_at.isoformat(),
                }
                for r in new_reflections
            ]
        }, status=status.HTTP_201_CREATED)


class AgentIntentsView(APIView):
    """AI 分身的意圖/目標"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, agent_id):
        """
        獲取 AI 分身的意圖列表
        GET /api/agent/<agent_id>/intents/
        Query params:
            - status: 過濾狀態 (pending, active, completed, expired)
            - limit: 最大數量 (default: 10)
        """
        agent = get_object_or_404(Agent, id=agent_id)

        if agent.user != request.user:
            return Response(
                {"message": "無權查看"},
                status=status.HTTP_403_FORBIDDEN
            )

        intent_status = request.query_params.get('status')
        limit = int(request.query_params.get('limit', 10))

        intents = intent_service.get_intents(
            str(agent_id),
            status=intent_status,
            limit=limit
        )

        return Response({
            "count": len(intents),
            "intents": intents
        })

    def post(self, request, agent_id):
        """
        創建新意圖
        POST /api/agent/<agent_id>/intents/
        Body:
            - goal: 目標描述 (required)
            - goal_type: 目標類型 (required)
            - target_agent_id: 目標 Agent ID (optional)
            - target_topic: 話題 (optional)
            - priority: 優先級 1-10 (default: 5)
            - expires_minutes: 過期時間分鐘 (default: 30)
        """
        agent = get_object_or_404(Agent, id=agent_id)

        if agent.user != request.user:
            return Response(
                {"message": "無權操作"},
                status=status.HTTP_403_FORBIDDEN
            )

        goal = request.data.get('goal')
        goal_type = request.data.get('goal_type')

        if not goal or not goal_type:
            return Response(
                {"message": "需要 goal 和 goal_type"},
                status=status.HTTP_400_BAD_REQUEST
            )

        valid_types = ['make_friend', 'chat_topic', 'explore_room', 'follow_up', 'rest', 'observe', 'socialize']
        if goal_type not in valid_types:
            return Response(
                {"message": f"無效的 goal_type，可選: {valid_types}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        intent = intent_service.create_intent(
            str(agent_id),
            goal=goal,
            goal_type=goal_type,
            target_agent_id=request.data.get('target_agent_id'),
            target_topic=request.data.get('target_topic', ''),
            priority=int(request.data.get('priority', 5)),
            expires_minutes=int(request.data.get('expires_minutes', 30))
        )

        if intent:
            return Response({
                "message": "意圖已創建",
                "intent": {
                    'id': str(intent.id),
                    'goal': intent.goal,
                    'goal_type': intent.goal_type,
                    'status': intent.status,
                    'steps': intent.steps,
                    'expires_at': intent.expires_at.isoformat(),
                }
            }, status=status.HTTP_201_CREATED)

        return Response(
            {"message": "創建失敗"},
            status=status.HTTP_400_BAD_REQUEST
        )


class AgentIntentDetailView(APIView):
    """單個意圖的操作"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, agent_id, intent_id):
        """獲取意圖詳情"""
        agent = get_object_or_404(Agent, id=agent_id)

        if agent.user != request.user:
            return Response(
                {"message": "無權查看"},
                status=status.HTTP_403_FORBIDDEN
            )

        intent = get_object_or_404(AgentIntent, id=intent_id, agent=agent)

        return Response({
            'id': str(intent.id),
            'goal': intent.goal,
            'goal_type': intent.goal_type,
            'status': intent.status,
            'priority': intent.priority,
            'steps': intent.steps,
            'current_step': intent.current_step,
            'current_step_name': intent.current_step_name,
            'progress_notes': intent.progress_notes,
            'target_agent_id': str(intent.target_agent_id) if intent.target_agent_id else None,
            'target_topic': intent.target_topic,
            'expires_at': intent.expires_at.isoformat(),
            'created_at': intent.created_at.isoformat(),
            'started_at': intent.started_at.isoformat() if intent.started_at else None,
            'completed_at': intent.completed_at.isoformat() if intent.completed_at else None,
        })

    def delete(self, request, agent_id, intent_id):
        """取消意圖"""
        agent = get_object_or_404(Agent, id=agent_id)

        if agent.user != request.user:
            return Response(
                {"message": "無權操作"},
                status=status.HTTP_403_FORBIDDEN
            )

        reason = request.data.get('reason', 'User cancelled')
        success = intent_service.cancel_intent(str(intent_id), reason)

        if success:
            return Response({"message": "意圖已取消"})

        return Response(
            {"message": "取消失敗"},
            status=status.HTTP_400_BAD_REQUEST
        )


class AgentActionsView(APIView):
    """AI 分身的行動佇列"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, agent_id):
        """
        獲取 AI 分身的行動佇列
        GET /api/agent/<agent_id>/actions/
        """
        from .models import AgentAction

        agent = get_object_or_404(Agent, id=agent_id)

        if agent.user != request.user:
            return Response(
                {"message": "無權查看"},
                status=status.HTTP_403_FORBIDDEN
            )

        limit = int(request.query_params.get('limit', 20))
        action_status = request.query_params.get('status')

        actions = AgentAction.objects.filter(agent=agent)
        if action_status:
            actions = actions.filter(status=action_status)

        actions = actions.order_by('-priority', '-created_at')[:limit]

        return Response({
            "count": actions.count(),
            "actions": [
                {
                    'id': str(a.id),
                    'action_type': a.action_type,
                    'target_location': a.target_location,
                    'target_agent_id': str(a.target_agent_id) if a.target_agent_id else None,
                    'parameters': a.parameters,
                    'priority': a.priority,
                    'status': a.status,
                    'created_at': a.created_at.isoformat(),
                }
                for a in actions
            ]
        })


class AgentInteractionsView(APIView):
    """AI 分身的交互日誌"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, agent_id):
        """
        獲取 AI 分身的交互日誌
        GET /api/agent/<agent_id>/interactions/
        Query params:
            - limit: 最大數量 (default: 50)
            - event_type: 過濾事件類型
        """
        agent = get_object_or_404(Agent, id=agent_id)

        if agent.user != request.user:
            return Response(
                {"message": "無權查看"},
                status=status.HTTP_403_FORBIDDEN
            )

        limit = int(request.query_params.get('limit', 50))
        event_type = request.query_params.get('event_type')

        logs = InteractionLog.objects.filter(agent=agent)
        if event_type:
            logs = logs.filter(event_type=event_type)

        logs = logs.select_related('target_agent', 'room').order_by('-created_at')[:limit]

        return Response({
            "count": logs.count(),
            "interactions": [
                {
                    'id': str(log.id),
                    'event_type': log.event_type,
                    'target_agent_id': str(log.target_agent_id) if log.target_agent_id else None,
                    'target_agent_name': log.target_agent.name if log.target_agent else None,
                    'room_id': str(log.room_id),
                    'room_name': log.room.name if log.room else None,
                    'payload': log.payload,
                    'location': {'x': log.location_x, 'y': log.location_y},
                    'created_at': log.created_at.isoformat(),
                }
                for log in logs
            ]
        })


class GenerateDailyGoalsView(APIView):
    """生成每日目標"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, agent_id):
        """
        為 AI 分身生成每日目標
        POST /api/agent/<agent_id>/daily-goals/
        """
        agent = get_object_or_404(Agent, id=agent_id)

        if agent.user != request.user:
            return Response(
                {"message": "無權操作"},
                status=status.HTTP_403_FORBIDDEN
            )

        language = request.user.preferred_language or 'zh-hant'

        intents = intent_service.generate_daily_goals(
            str(agent_id),
            language=language
        )

        return Response({
            "message": f"生成了 {len(intents)} 個每日目標",
            "goals": [
                {
                    'id': str(i.id),
                    'goal': i.goal,
                    'goal_type': i.goal_type,
                    'priority': i.priority,
                    'expires_at': i.expires_at.isoformat(),
                }
                for i in intents
            ]
        }, status=status.HTTP_201_CREATED)
