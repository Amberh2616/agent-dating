"""
配對系統 URL
Matching URLs
"""

from django.urls import path
from .views import (
    MatchRecommendationsView,
    MatchScoreView,
    MatchLikeView,
    MatchConnectView,
    MatchRequestsView,
)

urlpatterns = [
    path('recommendations/', MatchRecommendationsView.as_view(), name='match_recommendations'),
    path('score/<uuid:user_id>/', MatchScoreView.as_view(), name='match_score'),
    path('like/<uuid:user_id>/', MatchLikeView.as_view(), name='match_like'),
    path('connect/<uuid:user_id>/', MatchConnectView.as_view(), name='match_connect'),
    path('requests/', MatchRequestsView.as_view(), name='match_requests'),
]
