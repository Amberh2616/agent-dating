"""
用戶認證相關 URL
User Authentication URLs
"""

from django.urls import path
from .views import RegisterView, QuestionnaireView, QuestionnaireResponsesView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('questionnaire/', QuestionnaireView.as_view(), name='questionnaire'),
    path('questionnaire/responses/', QuestionnaireResponsesView.as_view(), name='questionnaire_responses'),
]
