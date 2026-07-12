"""
聊天系統視圖
Chat Views
"""

from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone

from .models import Conversation, Message, ConversationSummary
from apps.agents.models import Agent


class ConversationListView(APIView):
    """對話列表"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """獲取我的對話列表"""
        user = request.user

        # 獲取用戶參與的對話
        conversations = Conversation.objects.filter(
            Q(user_participant=user) | Q(other_user=user)
        ).order_by('-last_message_at')

        data = []
        for conv in conversations:
            # 確定對方
            if conv.conversation_type == 'user_to_agent':
                other_agent = conv.other_agent
                other_info = {
                    'type': 'agent',
                    'id': str(other_agent.id) if other_agent else None,
                    'name': other_agent.name if other_agent else 'Unknown',
                    'avatar': other_agent.avatar_look if other_agent else None,
                }
            elif conv.conversation_type == 'user_to_user':
                other_user = conv.other_user if conv.user_participant == user else conv.user_participant
                other_info = {
                    'type': 'user',
                    'id': str(other_user.id) if other_user else None,
                    'name': other_user.username if other_user else 'Unknown',
                }
            else:
                other_info = {'type': 'unknown'}

            data.append({
                'id': str(conv.id),
                'type': conv.conversation_type,
                'other': other_info,
                'last_message': conv.last_message_preview,
                'last_message_at': conv.last_message_at.isoformat() if conv.last_message_at else None,
                'unread_count': conv.unread_count,
                'message_count': conv.message_count,
            })

        return Response({'conversations': data})


class ConversationDetailView(APIView):
    """對話詳情"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, conversation_id):
        """獲取對話訊息"""
        user = request.user
        conversation = get_object_or_404(Conversation, id=conversation_id)

        # 檢查權限
        if conversation.user_participant != user and conversation.other_user != user:
            return Response(
                {"message": "無權訪問此對話"},
                status=status.HTTP_403_FORBIDDEN
            )

        # 分頁參數
        limit = int(request.query_params.get('limit', 50))
        before = request.query_params.get('before')  # message_id

        messages = conversation.messages.all()
        if before:
            try:
                before_msg = Message.objects.get(id=before)
                messages = messages.filter(created_at__lt=before_msg.created_at)
            except Message.DoesNotExist:
                pass

        messages = messages.order_by('-created_at')[:limit]

        data = []
        for msg in reversed(messages):
            sender_info = {}
            if msg.sender_type == 'user':
                sender_info = {
                    'type': 'user',
                    'id': str(msg.sender_user_id) if msg.sender_user_id else None,
                    'name': msg.sender_user.username if msg.sender_user else 'Unknown',
                }
            else:
                sender_info = {
                    'type': 'agent',
                    'id': str(msg.sender_agent_id) if msg.sender_agent_id else None,
                    'name': msg.sender_agent.name if msg.sender_agent else 'AI',
                }

            data.append({
                'id': str(msg.id),
                'sender': sender_info,
                'content': msg.content,
                'message_type': msg.message_type,
                'emotion': msg.emotion,
                'is_ai_generated': msg.is_ai_generated,
                'is_read': msg.is_read,
                'created_at': msg.created_at.isoformat(),
            })

        return Response({
            'conversation_id': str(conversation.id),
            'messages': data,
            'has_more': messages.count() == limit,
        })


class StartChatWithAgentView(APIView):
    """開始和某人的 AI 聊天"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, agent_id):
        """開始與指定 AI 分身的對話"""
        user = request.user
        agent = get_object_or_404(Agent, id=agent_id)

        # 不能和自己的 AI 聊天
        if agent.user == user:
            return Response(
                {"message": "無法與自己的 AI 分身聊天"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 查找或創建對話
        conversation, created = Conversation.objects.get_or_create(
            conversation_type='user_to_agent',
            user_participant=user,
            other_agent=agent
        )

        return Response({
            'conversation_id': str(conversation.id),
            'created': created,
            'agent': {
                'id': str(agent.id),
                'name': agent.name,
                'avatar_look': agent.avatar_look,
                'bio': agent.bio,
            }
        })


class SendMessageView(APIView):
    """發送訊息"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, conversation_id):
        """發送訊息到對話"""
        user = request.user
        conversation = get_object_or_404(Conversation, id=conversation_id)

        # 檢查權限
        if conversation.user_participant != user:
            return Response(
                {"message": "無權發送訊息"},
                status=status.HTTP_403_FORBIDDEN
            )

        content = request.data.get('content', '').strip()
        if not content:
            return Response(
                {"message": "訊息內容不能為空"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 創建訊息
        message = Message.objects.create(
            conversation=conversation,
            sender_type='user',
            sender_user=user,
            content=content,
            is_ai_generated=False
        )

        # 更新用戶的 Agent 的 last_chat_message (供前端顯示氣泡)
        try:
            from django.utils import timezone
            my_agent = user.agent
            my_agent.last_chat_message = content[:500]
            my_agent.last_chat_time = timezone.now()
            my_agent.save(update_fields=['last_chat_message', 'last_chat_time'])

            # 廣播氣泡到 World WebSocket
            from apps.world.models import AgentPosition
            from apps.world.utils import broadcast_agent_chat
            position = AgentPosition.objects.filter(agent=my_agent).first()
            if position and position.room:
                broadcast_agent_chat(str(position.room.id), str(my_agent.id), content[:500], duration=8000)
        except Exception:
            pass  # 用戶可能沒有 Agent

        # 觸發 AI 回覆 (如果是和 AI 對話，且模式為 AI)
        if conversation.conversation_type == 'user_to_agent' and conversation.mode == 'ai':
            from apps.agents.tasks import generate_agent_response
            generate_agent_response.delay(str(conversation.id))

        return Response({
            'message_id': str(message.id),
            'content': message.content,
            'created_at': message.created_at.isoformat(),
        })


class AIReportListView(APIView):
    """AI 代聊報告列表"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """
        獲取 AI 代聊報告

        Query params:
        - unread_only: 只返回未讀報告
        - limit: 返回數量限制 (默認 20)
        """
        user = request.user
        unread_only = request.query_params.get('unread_only', 'false').lower() == 'true'
        limit = int(request.query_params.get('limit', 20))

        # 獲取用戶的 Agent
        try:
            my_agent = Agent.objects.get(user=user)
        except Agent.DoesNotExist:
            return Response({'reports': [], 'unread_count': 0})

        # 獲取用戶參與的 AI-to-AI 對話
        conversations = Conversation.objects.filter(
            Q(agent_participant=my_agent) | Q(other_agent=my_agent),
            conversation_type='agent_to_agent'
        )

        # 獲取摘要
        summaries = ConversationSummary.objects.filter(
            conversation__in=conversations
        ).select_related('conversation').order_by('-created_at')

        if unread_only:
            summaries = summaries.filter(is_read=False)

        summaries = summaries[:limit]

        # 計算未讀數量
        unread_count = ConversationSummary.objects.filter(
            conversation__in=conversations,
            is_read=False
        ).count()

        reports = []
        for summary in summaries:
            conv = summary.conversation
            # 確定對方
            if conv.agent_participant == my_agent:
                other_agent = conv.other_agent
            else:
                other_agent = conv.agent_participant

            reports.append({
                'id': str(summary.id),
                'conversation_id': str(conv.id),
                'other_agent': {
                    'id': str(other_agent.id) if other_agent else None,
                    'name': other_agent.name if other_agent else 'Unknown',
                    'avatar_look': other_agent.avatar_look if other_agent else None,
                },
                'summary': summary.summary_text,
                'topics': summary.key_topics,
                'tone': summary.emotional_tone,
                'best_moment': summary.best_moment,
                'shared_interests': summary.shared_interests_found,
                'impression_score': summary.impression_score,
                'impression_delta': summary.impression_delta,
                'trend': summary.compatibility_trend,
                'message_count': summary.message_count,
                'period_start': summary.period_start.isoformat(),
                'period_end': summary.period_end.isoformat(),
                'is_read': summary.is_read,
                'created_at': summary.created_at.isoformat(),
            })

        return Response({
            'reports': reports,
            'unread_count': unread_count,
        })


class AIReportDetailView(APIView):
    """AI 報告詳情"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, report_id):
        """獲取報告詳情並標記為已讀"""
        user = request.user
        summary = get_object_or_404(ConversationSummary, id=report_id)

        # 驗證權限
        conv = summary.conversation
        try:
            my_agent = Agent.objects.get(user=user)
            if conv.agent_participant != my_agent and conv.other_agent != my_agent:
                return Response(
                    {"message": "無權訪問此報告"},
                    status=status.HTTP_403_FORBIDDEN
                )
        except Agent.DoesNotExist:
            return Response(
                {"message": "無權訪問此報告"},
                status=status.HTTP_403_FORBIDDEN
            )

        # 標記為已讀
        if not summary.is_read:
            summary.is_read = True
            summary.save(update_fields=['is_read'])

        # 確定對方
        if conv.agent_participant == my_agent:
            other_agent = conv.other_agent
        else:
            other_agent = conv.agent_participant

        return Response({
            'id': str(summary.id),
            'conversation_id': str(conv.id),
            'other_agent': {
                'id': str(other_agent.id) if other_agent else None,
                'name': other_agent.name if other_agent else 'Unknown',
                'avatar_look': other_agent.avatar_look if other_agent else None,
            },
            'summary': summary.summary_text,
            'topics': summary.key_topics,
            'tone': summary.emotional_tone,
            'best_moment': summary.best_moment,
            'shared_interests': summary.shared_interests_found,
            'impression_score': summary.impression_score,
            'impression_delta': summary.impression_delta,
            'trend': summary.compatibility_trend,
            'message_count': summary.message_count,
            'period_start': summary.period_start.isoformat(),
            'period_end': summary.period_end.isoformat(),
            'is_read': summary.is_read,
            'created_at': summary.created_at.isoformat(),
        })


class ConversationModeView(APIView):
    """切換對話模式"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, conversation_id):
        """獲取當前對話模式"""
        user = request.user
        conversation = get_object_or_404(Conversation, id=conversation_id)

        # 驗證權限
        if conversation.user_participant != user:
            # 檢查是否是 agent_to_agent 對話
            try:
                my_agent = Agent.objects.get(user=user)
                if conversation.agent_participant != my_agent and conversation.other_agent != my_agent:
                    return Response(
                        {"message": "無權訪問此對話"},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except Agent.DoesNotExist:
                return Response(
                    {"message": "無權訪問此對話"},
                    status=status.HTTP_403_FORBIDDEN
                )

        return Response({
            'conversation_id': str(conversation.id),
            'mode': conversation.mode,
            'mode_changed_at': conversation.mode_changed_at.isoformat() if conversation.mode_changed_at else None,
        })

    def post(self, request, conversation_id):
        """
        切換對話模式

        Body:
        - mode: 'ai' | 'user' | 'paused'
        """
        user = request.user
        conversation = get_object_or_404(Conversation, id=conversation_id)

        # 驗證權限
        if conversation.user_participant != user:
            try:
                my_agent = Agent.objects.get(user=user)
                if conversation.agent_participant != my_agent and conversation.other_agent != my_agent:
                    return Response(
                        {"message": "無權修改此對話"},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except Agent.DoesNotExist:
                return Response(
                    {"message": "無權修改此對話"},
                    status=status.HTTP_403_FORBIDDEN
                )

        new_mode = request.data.get('mode')
        valid_modes = ['ai', 'user', 'paused']

        if new_mode not in valid_modes:
            return Response(
                {"message": f"無效的模式，請選擇: {', '.join(valid_modes)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        old_mode = conversation.mode
        conversation.mode = new_mode
        conversation.mode_changed_at = timezone.now()
        conversation.save(update_fields=['mode', 'mode_changed_at'])

        mode_labels = {
            'ai': 'AI 代聊',
            'user': '用戶親自',
            'paused': '暫停',
        }

        return Response({
            'conversation_id': str(conversation.id),
            'mode': new_mode,
            'mode_label': mode_labels.get(new_mode, new_mode),
            'previous_mode': old_mode,
            'mode_changed_at': conversation.mode_changed_at.isoformat(),
            'message': f'已切換為「{mode_labels.get(new_mode, new_mode)}」模式',
        })


class ConversationImpressionView(APIView):
    """印象分歷史"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, conversation_id):
        """獲取印象分歷史"""
        user = request.user
        conversation = get_object_or_404(Conversation, id=conversation_id)

        # 驗證權限
        if conversation.user_participant != user:
            try:
                my_agent = Agent.objects.get(user=user)
                if conversation.agent_participant != my_agent and conversation.other_agent != my_agent:
                    return Response(
                        {"message": "無權訪問此對話"},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except Agent.DoesNotExist:
                return Response(
                    {"message": "無權訪問此對話"},
                    status=status.HTTP_403_FORBIDDEN
                )

        # 獲取所有摘要的印象分
        summaries = ConversationSummary.objects.filter(
            conversation=conversation
        ).order_by('created_at').values(
            'id', 'impression_score', 'impression_delta',
            'compatibility_trend', 'created_at'
        )

        history = []
        for s in summaries:
            history.append({
                'id': str(s['id']),
                'score': s['impression_score'],
                'delta': s['impression_delta'],
                'trend': s['compatibility_trend'],
                'date': s['created_at'].isoformat(),
            })

        # 當前分數
        current_score = history[-1]['score'] if history else 50

        return Response({
            'conversation_id': str(conversation.id),
            'current_score': current_score,
            'history': history,
        })
