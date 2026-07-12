from django.contrib import admin
from .models import Room, AgentPosition, WorldEvent


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'room_type', 'is_visible', 'max_capacity', 'created_at')
    list_filter = ('room_type', 'is_visible')
    search_fields = ('name', 'description')


@admin.register(AgentPosition)
class AgentPositionAdmin(admin.ModelAdmin):
    list_display = ('agent', 'room', 'x', 'y', 'direction', 'updated_at')
    list_filter = ('room',)
    search_fields = ('agent__name',)


@admin.register(WorldEvent)
class WorldEventAdmin(admin.ModelAdmin):
    list_display = ('room', 'event_type', 'created_at')
    list_filter = ('event_type', 'room')
    readonly_fields = ('created_at',)
