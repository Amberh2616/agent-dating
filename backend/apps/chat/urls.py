"""
聊天系統 URL
Chat URLs
"""

from django.urls import path
from .views import (
    ConversationListView,
    ConversationDetailView,
    StartChatWithAgentView,
    SendMessageView,
    AIReportListView,
    AIReportDetailView,
    ConversationModeView,
    ConversationImpressionView,
)

urlpatterns = [
    # 對話
    path('conversations/', ConversationListView.as_view(), name='conversation_list'),
    path('conversations/<uuid:conversation_id>/', ConversationDetailView.as_view(), name='conversation_detail'),
    path('conversations/<uuid:conversation_id>/send/', SendMessageView.as_view(), name='send_message'),
    path('conversations/<uuid:conversation_id>/mode/', ConversationModeView.as_view(), name='conversation_mode'),
    path('conversations/<uuid:conversation_id>/impression/', ConversationImpressionView.as_view(), name='conversation_impression'),
    path('start/<uuid:agent_id>/', StartChatWithAgentView.as_view(), name='start_chat'),

    # AI 代聊報告
    path('ai-reports/', AIReportListView.as_view(), name='ai_report_list'),
    path('ai-reports/<uuid:report_id>/', AIReportDetailView.as_view(), name='ai_report_detail'),
]
