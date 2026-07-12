"""
虛擬世界視圖
World Views
"""

from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Room, AgentPosition


class RoomListView(APIView):
    """房間列表"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """獲取所有公開房間"""
        room_type = request.query_params.get('type')

        rooms = Room.objects.filter(is_active=True, is_visible=True)
        if room_type:
            rooms = rooms.filter(room_type=room_type)

        rooms = rooms.order_by('-visit_count')

        data = []
        for room in rooms:
            # 獲取房間內的 agent 數量
            agent_count = AgentPosition.objects.filter(room=room).count()

            data.append({
                'id': str(room.id),
                'name': room.name,
                'description': room.description,
                'type': room.room_type,
                'type_display': dict(Room.ROOM_TYPES).get(room.room_type),
                'width': room.width,
                'height': room.height,
                'max_capacity': room.max_capacity,
                'current_agents': agent_count,
                'visit_count': room.visit_count,
            })

        return Response({'rooms': data})


class RoomDetailView(APIView):
    """房間詳情"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, room_id):
        """獲取房間詳情"""
        room = get_object_or_404(Room, id=room_id)

        # 獲取房間內的 agents
        positions = AgentPosition.objects.filter(room=room).select_related('agent')

        agents = []
        for pos in positions:
            agents.append({
                'id': str(pos.agent.id),
                'name': pos.agent.name,
                'avatar_look': pos.agent.avatar_look,
                'x': pos.x,
                'y': pos.y,
                'direction': pos.direction,
                'action': pos.agent.current_action,
                'emotion': pos.agent.current_emotion,
            })

        return Response({
            'room': {
                'id': str(room.id),
                'name': room.name,
                'description': room.description,
                'type': room.room_type,
                'width': room.width,
                'height': room.height,
                'floor_plan': room.floor_plan,
                'spawn_points': room.spawn_points,
                'furniture': room.furniture,
            },
            'agents': agents,
        })


class RoomAgentsView(APIView):
    """房間內的 Agents"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, room_id):
        """獲取房間內的所有 agents"""
        room = get_object_or_404(Room, id=room_id)

        positions = AgentPosition.objects.filter(room=room).select_related('agent')

        agents = []
        for pos in positions:
            # 檢查訊息是否在 60 秒內
            chat_message = ''
            if pos.agent.last_chat_message and pos.agent.last_chat_time:
                from django.utils import timezone
                from datetime import timedelta
                if timezone.now() - pos.agent.last_chat_time < timedelta(seconds=60):
                    chat_message = pos.agent.last_chat_message

            agents.append({
                'id': str(pos.agent.id),
                'name': pos.agent.name,
                'avatar_look': pos.agent.avatar_look,
                'x': pos.x,
                'y': pos.y,
                'direction': pos.direction,
                'action': pos.agent.current_action,
                'emotion': pos.agent.current_emotion,
                'is_online': pos.agent.is_online,
                'chat_message': chat_message,  # 最近的對話訊息
            })

        return Response({'agents': agents})


class MoveAgentView(APIView):
    """移動 AI 分身"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """移動我的 AI 分身"""
        user = request.user

        try:
            agent = user.agent
        except Exception:
            return Response(
                {"message": "尚未創建 AI 分身"},
                status=status.HTTP_400_BAD_REQUEST
            )

        x = request.data.get('x')
        y = request.data.get('y')
        room_id = request.data.get('room_id')

        if x is None or y is None:
            return Response(
                {"message": "請提供目標座標"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 獲取或創建位置
        try:
            position = agent.position
        except AgentPosition.DoesNotExist:
            if not room_id:
                return Response(
                    {"message": "請提供房間 ID"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            room = get_object_or_404(Room, id=room_id)
            position = AgentPosition.objects.create(agent=agent, room=room)

        # 更新目標位置
        position.target_x = x
        position.target_y = y
        position.is_moving = True
        position.save()

        return Response({
            'message': '移動指令已發送',
            'target': {'x': x, 'y': y}
        })


class AgentActionView(APIView):
    """AI 分身動作"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """執行 AI 分身動作"""
        user = request.user

        try:
            agent = user.agent
        except Exception:
            return Response(
                {"message": "尚未創建 AI 分身"},
                status=status.HTTP_400_BAD_REQUEST
            )

        action = request.data.get('action')
        valid_actions = ['wave', 'sit', 'stand', 'dance', 'idle']

        if action not in valid_actions:
            return Response(
                {"message": f"無效的動作，可選：{valid_actions}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        agent.current_action = action
        agent.save()

        return Response({
            'message': f'執行動作：{action}',
            'action': action
        })
