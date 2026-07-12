"""
關係系統 URL
Relationship URLs
"""

from django.urls import path
from .views import (
    RelationshipsListView,
    RelationshipDetailView,
    SendGiftView,
    ConfessionView,
)

urlpatterns = [
    path('', RelationshipsListView.as_view(), name='relationships_list'),
    path('<uuid:user_id>/', RelationshipDetailView.as_view(), name='relationship_detail'),
    path('<uuid:user_id>/gift/', SendGiftView.as_view(), name='send_gift'),
    path('<uuid:user_id>/confess/', ConfessionView.as_view(), name='confession'),
]
