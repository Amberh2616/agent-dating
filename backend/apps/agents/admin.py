from django.contrib import admin
from .models import Agent, Memory, DailyPlan, AgentAction


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'is_online', 'current_emotion', 'last_active')
    list_filter = ('is_online', 'current_emotion')
    search_fields = ('name', 'user__email')
    readonly_fields = ('created_at', 'last_active')


@admin.register(Memory)
class MemoryAdmin(admin.ModelAdmin):
    list_display = ('agent', 'type', 'importance', 'created_at')
    list_filter = ('type', 'importance')
    search_fields = ('agent__name', 'content')
    readonly_fields = ('created_at',)


@admin.register(DailyPlan)
class DailyPlanAdmin(admin.ModelAdmin):
    list_display = ('agent', 'date', 'created_at')
    list_filter = ('date',)
    search_fields = ('agent__name',)


@admin.register(AgentAction)
class AgentActionAdmin(admin.ModelAdmin):
    list_display = ('agent', 'action_type', 'status', 'created_at')
    list_filter = ('action_type', 'status')
    search_fields = ('agent__name',)
