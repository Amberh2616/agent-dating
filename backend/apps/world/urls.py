"""
虛擬世界 URL
World URLs
"""

from django.urls import path
from .views import (
    RoomListView,
    RoomDetailView,
    RoomAgentsView,
    MoveAgentView,
    AgentActionView,
)

urlpatterns = [
    path('rooms/', RoomListView.as_view(), name='room_list'),
    path('room/<uuid:room_id>/', RoomDetailView.as_view(), name='room_detail'),
    path('room/<uuid:room_id>/agents/', RoomAgentsView.as_view(), name='room_agents'),
    path('agent/move/', MoveAgentView.as_view(), name='move_agent'),
    path('agent/action/', AgentActionView.as_view(), name='agent_action'),
]
