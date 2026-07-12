"""
URL configuration for Agent Dating project.
代理交友 API 路由配置
"""

from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # JWT Authentication
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # App APIs
    path('api/auth/', include('apps.users.urls')),
    path('api/user/', include('apps.users.urls_profile')),
    path('api/agent/', include('apps.agents.urls')),
    path('api/match/', include('apps.matching.urls')),
    path('api/relationship/', include('apps.relationships.urls')),
    path('api/chat/', include('apps.chat.urls')),
    path('api/world/', include('apps.world.urls')),
]
