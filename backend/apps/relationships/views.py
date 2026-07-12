"""
關係系統視圖
Relationship Views
"""

from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import Relationship, RelationshipEvent, Gift

User = get_user_model()


class RelationshipsListView(APIView):
    """我的關係列表"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """獲取所有關係"""
        user = request.user
        stage_filter = request.query_params.get('stage')

        relationships = Relationship.objects.filter(
            Q(user_a=user) | Q(user_b=user)
        )

        if stage_filter:
            relationships = relationships.filter(stage=stage_filter)

        relationships = relationships.order_by('-closeness')

        data = []
        for rel in relationships:
            other_user = rel.user_b if rel.user_a == user else rel.user_a

            # 獲取對方的 AI 分身
            try:
                agent = other_user.agent
                agent_data = {
                    'id': str(agent.id),
                    'name': agent.name,
                    'avatar_look': agent.avatar_look,
                }
            except Exception:
                agent_data = None

            data.append({
                'id': str(rel.id),
                'other_user': {
                    'id': str(other_user.id),
                    'username': other_user.username,
                },
                'agent': agent_data,
                'stage': rel.stage,
                'stage_display': dict(Relationship.STAGES).get(rel.stage, rel.stage),
                'closeness': rel.closeness,
                'trust': rel.trust,
                'romantic': rel.romantic,
                'interaction_count': rel.interaction_count,
                'first_met': rel.first_met.isoformat(),
                'last_interaction': rel.last_interaction.isoformat(),
            })

        return Response({'relationships': data})


class RelationshipDetailView(APIView):
    """關係詳情"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, user_id):
        """獲取與指定用戶的關係"""
        user = request.user
        other_user = get_object_or_404(User, id=user_id)

        if user == other_user:
            return Response(
                {"message": "無法查看與自己的關係"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 確保 user_a.id < user_b.id
        user_a, user_b = (user, other_user) if user.id < other_user.id else (other_user, user)

        try:
            relationship = Relationship.objects.get(user_a=user_a, user_b=user_b)
        except Relationship.DoesNotExist:
            return Response(
                {"message": "尚無關係記錄"},
                status=status.HTTP_404_NOT_FOUND
            )

        # 獲取關係事件
        events = RelationshipEvent.objects.filter(
            relationship=relationship
        ).order_by('-created_at')[:20]

        return Response({
            'id': str(relationship.id),
            'stage': relationship.stage,
            'stage_display': dict(Relationship.STAGES).get(relationship.stage),
            'closeness': relationship.closeness,
            'trust': relationship.trust,
            'romantic': relationship.romantic,
            'interaction_count': relationship.interaction_count,
            'ai_interaction_count': relationship.ai_interaction_count,
            'real_interaction_count': relationship.real_interaction_count,
            'first_met': relationship.first_met.isoformat(),
            'became_friends_at': relationship.became_friends_at.isoformat() if relationship.became_friends_at else None,
            'became_lovers_at': relationship.became_lovers_at.isoformat() if relationship.became_lovers_at else None,
            'description': relationship.description,
            'shared_memories': relationship.shared_memories,
            'events': [
                {
                    'type': e.event_type,
                    'title': e.title,
                    'description': e.description,
                    'created_at': e.created_at.isoformat(),
                }
                for e in events
            ],
        })


class SendGiftView(APIView):
    """送禮物"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, user_id):
        """送禮物給某人"""
        user = request.user
        receiver = get_object_or_404(User, id=user_id)

        if user == receiver:
            return Response(
                {"message": "無法送禮物給自己"},
                status=status.HTTP_400_BAD_REQUEST
            )

        gift_type = request.data.get('gift_type')
        message = request.data.get('message', '')

        valid_types = [t[0] for t in Gift.GIFT_TYPES]
        if gift_type not in valid_types:
            return Response(
                {"message": f"無效的禮物類型，可選：{valid_types}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 創建禮物
        gift = Gift.objects.create(
            sender=user,
            receiver=receiver,
            gift_type=gift_type,
            message=message
        )

        # 更新關係 (增加親密度和浪漫值)
        user_a, user_b = (user, receiver) if user.id < receiver.id else (receiver, user)
        relationship, created = Relationship.objects.get_or_create(
            user_a=user_a,
            user_b=user_b
        )

        relationship.closeness = min(100, relationship.closeness + 3)
        relationship.romantic = min(100, relationship.romantic + 5)
        relationship.interaction_count += 1
        relationship.update_stage()

        # 記錄事件
        RelationshipEvent.objects.create(
            relationship=relationship,
            event_type='gift',
            title=f'送出{dict(Gift.GIFT_TYPES).get(gift_type)}',
            description=message,
            triggered_by=user,
            metadata={'gift_type': gift_type}
        )

        return Response({
            'message': '禮物已送出',
            'gift_id': str(gift.id),
            'closeness': relationship.closeness,
            'romantic': relationship.romantic,
        })


class ConfessionView(APIView):
    """告白"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, user_id):
        """向某人告白"""
        user = request.user
        target = get_object_or_404(User, id=user_id)

        if user == target:
            return Response(
                {"message": "無法向自己告白"},
                status=status.HTTP_400_BAD_REQUEST
            )

        message = request.data.get('message', '')

        # 獲取關係
        user_a, user_b = (user, target) if user.id < target.id else (target, user)
        relationship, created = Relationship.objects.get_or_create(
            user_a=user_a,
            user_b=user_b
        )

        # 記錄告白事件
        RelationshipEvent.objects.create(
            relationship=relationship,
            event_type='confession',
            title='告白',
            description=message,
            triggered_by=user
        )

        # 增加浪漫值
        relationship.romantic = min(100, relationship.romantic + 20)
        relationship.save()

        return Response({
            'message': '告白已送出',
            'romantic': relationship.romantic,
        })
