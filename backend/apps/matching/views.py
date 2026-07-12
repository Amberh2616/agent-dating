"""
配對系統視圖
Matching Views
"""

from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.contrib.auth import get_user_model

from .models import MatchScore, MatchInterest, MatchRequest
from .engine import matching_engine
from apps.users.models import SoulProfile

User = get_user_model()


class MatchRecommendationsView(APIView):
    """配對推薦列表"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """獲取配對推薦"""
        user = request.user
        limit = int(request.query_params.get('limit', 20))

        # 獲取用戶的靈魂檔案
        try:
            my_profile = user.soul_profile
        except SoulProfile.DoesNotExist:
            return Response(
                {"message": "請先完成靈魂問卷"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 獲取已有的配對分數
        existing_scores = MatchScore.objects.filter(
            Q(user_a=user) | Q(user_b=user)
        ).order_by('-total_score')[:limit]

        recommendations = []
        for score in existing_scores:
            other_user = score.user_b if score.user_a == user else score.user_a

            # 檢查是否有 AI 分身
            try:
                agent = other_user.agent
                agent_data = {
                    'id': str(agent.id),
                    'name': agent.name,
                    'avatar_look': agent.avatar_look,
                    'bio': agent.bio,
                }
            except Exception:
                agent_data = None

            recommendations.append({
                'user_id': str(other_user.id),
                'username': other_user.username,
                'match_score': score.total_score,
                'highlights': score.highlights,
                'breakdown': {
                    'worldview': score.worldview_score,
                    'lifeview': score.lifeview_score,
                    'values': score.values_score,
                    'interests': score.interests_score,
                    'personality': score.personality_score,
                    'communication': score.communication_score,
                    'emotional': score.emotional_score,
                },
                'has_dealbreaker': score.has_dealbreaker,
                'agent': agent_data,
            })

        return Response({
            'recommendations': recommendations,
            'total': len(recommendations)
        })


class MatchScoreView(APIView):
    """查看與某人的配對分數"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, user_id):
        """獲取與指定用戶的配對分數"""
        user = request.user
        target_user = get_object_or_404(User, id=user_id)

        if user == target_user:
            return Response(
                {"message": "無法與自己配對"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 確保 user_a.id < user_b.id
        user_a, user_b = (user, target_user) if user.id < target_user.id else (target_user, user)

        # 查找或計算配對分數
        try:
            score = MatchScore.objects.get(user_a=user_a, user_b=user_b)
        except MatchScore.DoesNotExist:
            # 計算配對分數
            score = self._calculate_and_save_score(user_a, user_b)
            if not score:
                return Response(
                    {"message": "無法計算配對分數，請確保雙方都已完成靈魂問卷"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return Response({
            'total_score': score.total_score,
            'highlights': score.highlights,
            'breakdown': {
                'worldview': score.worldview_score,
                'lifeview': score.lifeview_score,
                'values': score.values_score,
                'interests': score.interests_score,
                'personality': score.personality_score,
                'communication': score.communication_score,
                'emotional': score.emotional_score,
            },
            'has_dealbreaker': score.has_dealbreaker,
            'dealbreaker_reason': score.dealbreaker_reason,
        })

    def _calculate_and_save_score(self, user_a, user_b):
        """計算並儲存配對分數"""
        try:
            profile_a = user_a.soul_profile
            profile_b = user_b.soul_profile
        except SoulProfile.DoesNotExist:
            return None

        # 構建配對資料
        data_a = {
            'worldview': profile_a.worldview,
            'lifeview': profile_a.lifeview,
            'values': profile_a.values,
            'interests': profile_a.interests,
            'personality': profile_a.personality,
            'communication_style': profile_a.communication_style,
            'emotional_needs': profile_a.emotional_needs,
        }
        data_b = {
            'worldview': profile_b.worldview,
            'lifeview': profile_b.lifeview,
            'values': profile_b.values,
            'interests': profile_b.interests,
            'personality': profile_b.personality,
            'communication_style': profile_b.communication_style,
            'emotional_needs': profile_b.emotional_needs,
        }

        # 計算
        result = matching_engine.calculate_match(data_a, data_b)

        # 儲存
        score = MatchScore.objects.create(
            user_a=user_a,
            user_b=user_b,
            total_score=result.score,
            worldview_score=result.breakdown.get('worldview', 0),
            lifeview_score=result.breakdown.get('lifeview', 0),
            values_score=result.breakdown.get('values', 0),
            interests_score=result.breakdown.get('interests', 0),
            personality_score=result.breakdown.get('personality', 0),
            communication_score=result.breakdown.get('communication', 0),
            emotional_score=result.breakdown.get('emotional', 0),
            highlights=result.highlights,
            has_dealbreaker=result.has_dealbreaker,
            dealbreaker_reason=result.dealbreaker_reason,
        )

        return score


class MatchLikeView(APIView):
    """表達對某人的興趣"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, user_id):
        """對某人表示興趣"""
        user = request.user
        target_user = get_object_or_404(User, id=user_id)

        if user == target_user:
            return Response(
                {"message": "無法對自己表示興趣"},
                status=status.HTTP_400_BAD_REQUEST
            )

        interest, created = MatchInterest.objects.update_or_create(
            user=user,
            target_user=target_user,
            defaults={'status': 'liked'}
        )

        # 檢查是否互相喜歡
        mutual = MatchInterest.objects.filter(
            user=target_user,
            target_user=user,
            status='liked'
        ).exists()

        return Response({
            'message': '已表示興趣',
            'mutual_match': mutual,
        })


class MatchConnectView(APIView):
    """請求真人連結"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, user_id):
        """請求與某人的真人對話"""
        user = request.user
        target_user = get_object_or_404(User, id=user_id)

        if user == target_user:
            return Response(
                {"message": "無法與自己連結"},
                status=status.HTTP_400_BAD_REQUEST
            )

        message = request.data.get('message', '')

        # 創建連結請求
        match_request, created = MatchRequest.objects.get_or_create(
            requester=user,
            target=target_user,
            defaults={
                'message': message,
                'status': 'pending'
            }
        )

        if not created:
            return Response(
                {"message": "已發送過連結請求"},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response({
            'message': '連結請求已發送',
            'request_id': str(match_request.id)
        })


class MatchRequestsView(APIView):
    """我收到的連結請求"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """獲取收到的連結請求"""
        requests = MatchRequest.objects.filter(
            target=request.user,
            status='pending'
        ).select_related('requester')

        data = []
        for req in requests:
            data.append({
                'id': str(req.id),
                'requester': {
                    'id': str(req.requester.id),
                    'username': req.requester.username,
                },
                'message': req.message,
                'created_at': req.created_at.isoformat(),
            })

        return Response({'requests': data})

    def post(self, request):
        """回應連結請求"""
        request_id = request.data.get('request_id')
        action = request.data.get('action')  # accept or reject

        if action not in ['accept', 'reject']:
            return Response(
                {"message": "無效的操作"},
                status=status.HTTP_400_BAD_REQUEST
            )

        match_request = get_object_or_404(
            MatchRequest,
            id=request_id,
            target=request.user,
            status='pending'
        )

        from django.utils import timezone
        match_request.status = 'accepted' if action == 'accept' else 'rejected'
        match_request.responded_at = timezone.now()
        match_request.save()

        if action == 'accept':
            # 創建真人對話 (TODO: 實現)
            pass

        return Response({
            'message': f'已{"接受" if action == "accept" else "拒絕"}連結請求'
        })
