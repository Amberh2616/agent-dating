"""
AI 分身 URL
Agent URLs

Includes Generative Agents endpoints for:
- Memories, Reflections, Intents, Actions, Interactions
"""

from django.urls import path
from .views import (
    MyAgentView,
    AgentDetailView,
    AgentMemoriesView,
    AgentAutonomyView,
    # Generative Agents
    AgentReflectionsView,
    AgentIntentsView,
    AgentIntentDetailView,
    AgentActionsView,
    AgentInteractionsView,
    GenerateDailyGoalsView,
)

urlpatterns = [
    # Basic Agent endpoints
    path('me/', MyAgentView.as_view(), name='my_agent'),
    path('autonomy/', AgentAutonomyView.as_view(), name='agent_autonomy'),
    path('<uuid:agent_id>/', AgentDetailView.as_view(), name='agent_detail'),
    path('<uuid:agent_id>/memories/', AgentMemoriesView.as_view(), name='agent_memories'),

    # Generative Agents endpoints
    path('<uuid:agent_id>/reflections/', AgentReflectionsView.as_view(), name='agent_reflections'),
    path('<uuid:agent_id>/intents/', AgentIntentsView.as_view(), name='agent_intents'),
    path('<uuid:agent_id>/intents/<uuid:intent_id>/', AgentIntentDetailView.as_view(), name='agent_intent_detail'),
    path('<uuid:agent_id>/actions/', AgentActionsView.as_view(), name='agent_actions'),
    path('<uuid:agent_id>/interactions/', AgentInteractionsView.as_view(), name='agent_interactions'),
    path('<uuid:agent_id>/daily-goals/', GenerateDailyGoalsView.as_view(), name='agent_daily_goals'),
]
