"""
用戶相關序列化器
User Serializers
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import SoulProfile, QuestionnaireResponse

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """用戶基本資料序列化器"""

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'avatar_url', 'bio',
            'gender', 'birthday', 'location', 'preferred_language',
            'is_verified', 'is_premium', 'onboarding_completed',
            'created_at', 'last_active'
        ]
        read_only_fields = ['id', 'email', 'created_at', 'last_active']


class UserRegisterSerializer(serializers.ModelSerializer):
    """用戶註冊序列化器"""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'password_confirm']

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "密碼不一致"})
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=password
        )
        # 創建空白靈魂檔案
        SoulProfile.objects.create(user=user)
        return user


class SoulProfileSerializer(serializers.ModelSerializer):
    """靈魂檔案序列化器"""

    class Meta:
        model = SoulProfile
        fields = [
            'id', 'worldview', 'lifeview', 'values',
            'interests', 'personality', 'communication_style',
            'emotional_needs', 'love_style', 'relationship_behavior',
            'questionnaire_completed', 'analysis_completed',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class QuestionnaireResponseSerializer(serializers.ModelSerializer):
    """問卷回應序列化器"""

    class Meta:
        model = QuestionnaireResponse
        fields = ['id', 'question_id', 'question_text', 'answer', 'category', 'created_at']
        read_only_fields = ['id', 'created_at']


class QuestionnaireSubmitSerializer(serializers.Serializer):
    """問卷提交序列化器"""
    responses = serializers.ListField(
        child=serializers.DictField(),
        help_text='[{"question_id": 1, "answer": "..."}]'
    )

    def validate_responses(self, value):
        from .questionnaire import validate_answer, get_question_by_id

        for response in value:
            q_id = response.get('question_id')
            answer = response.get('answer')

            if not q_id:
                raise serializers.ValidationError(f"缺少 question_id")

            question = get_question_by_id(q_id)
            if not question:
                raise serializers.ValidationError(f"問題 {q_id} 不存在")

            if not validate_answer(q_id, answer):
                raise serializers.ValidationError(f"問題 {q_id} 答案格式不正確")

        return value
