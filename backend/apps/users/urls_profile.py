"""
用戶資料相關 URL
User Profile URLs
"""

from django.urls import path
from .views import UserProfileView, SoulProfileView

urlpatterns = [
    path('profile/', UserProfileView.as_view(), name='user_profile'),
    path('soul-profile/', SoulProfileView.as_view(), name='soul_profile'),
]
