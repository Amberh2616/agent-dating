"""
用戶相關視圖
User Views
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model

from .models import SoulProfile, QuestionnaireResponse
from .serializers import (
    UserSerializer,
    UserRegisterSerializer,
    SoulProfileSerializer,
    QuestionnaireResponseSerializer,
    QuestionnaireSubmitSerializer,
)
from .questionnaire import get_questionnaire, questionnaire_analyzer

User = get_user_model()


class RegisterView(APIView):
    """用戶註冊"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "message": "註冊成功",
                "user_id": str(user.id)
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    """用戶個人資料"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SoulProfileView(APIView):
    """靈魂檔案"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            profile = request.user.soul_profile
        except SoulProfile.DoesNotExist:
            profile = SoulProfile.objects.create(user=request.user)

        serializer = SoulProfileSerializer(profile)
        return Response(serializer.data)

    def put(self, request):
        try:
            profile = request.user.soul_profile
        except SoulProfile.DoesNotExist:
            profile = SoulProfile.objects.create(user=request.user)

        serializer = SoulProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class QuestionnaireView(APIView):
    """問卷系統"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """獲取問卷題目"""
        questionnaire = get_questionnaire()
        return Response({
            "questionnaire": questionnaire,
            "total_questions": len(questionnaire)
        })

    def post(self, request):
        """提交問卷回答"""
        serializer = QuestionnaireSubmitSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        responses = serializer.validated_data['responses']

        # 儲存回答
        for response in responses:
            from .questionnaire import get_question_by_id
            question = get_question_by_id(response['question_id'])

            QuestionnaireResponse.objects.update_or_create(
                user=request.user,
                question_id=response['question_id'],
                defaults={
                    'question_text': question['question'],
                    'answer': str(response['answer']),
                    'category': question['category']
                }
            )

        # 分析問卷生成靈魂檔案
        analyzed_profile = questionnaire_analyzer.analyze(responses)

        # 更新靈魂檔案
        try:
            profile = request.user.soul_profile
        except SoulProfile.DoesNotExist:
            profile = SoulProfile.objects.create(user=request.user)

        # 更新各個字段
        for key, value in analyzed_profile.items():
            if hasattr(profile, key):
                setattr(profile, key, value)

        profile.questionnaire_completed = True
        profile.save()

        # 標記用戶已完成入職
        request.user.onboarding_completed = True
        request.user.save()

        return Response({
            "message": "問卷提交成功",
            "soul_profile": SoulProfileSerializer(profile).data
        })


class QuestionnaireResponsesView(APIView):
    """用戶的問卷回答記錄"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        responses = QuestionnaireResponse.objects.filter(user=request.user)
        serializer = QuestionnaireResponseSerializer(responses, many=True)
        return Response(serializer.data)
