from django.contrib import admin
from .models import Relationship, RelationshipEvent, Gift


@admin.register(Relationship)
class RelationshipAdmin(admin.ModelAdmin):
    list_display = ('user_a', 'user_b', 'stage', 'closeness', 'first_met')
    list_filter = ('stage',)
    search_fields = ('user_a__email', 'user_b__email')
    readonly_fields = ('first_met',)


@admin.register(RelationshipEvent)
class RelationshipEventAdmin(admin.ModelAdmin):
    list_display = ('relationship', 'event_type', 'created_at')
    list_filter = ('event_type',)
    readonly_fields = ('created_at',)


@admin.register(Gift)
class GiftAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'gift_type', 'created_at')
    list_filter = ('gift_type',)
    search_fields = ('sender__email', 'receiver__email')
