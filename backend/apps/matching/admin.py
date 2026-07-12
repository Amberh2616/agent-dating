from django.contrib import admin
from .models import MatchScore, MatchInterest, MatchRequest


@admin.register(MatchScore)
class MatchScoreAdmin(admin.ModelAdmin):
    list_display = ('user_a', 'user_b', 'total_score', 'calculated_at')
    list_filter = ('calculated_at',)
    search_fields = ('user_a__email', 'user_b__email')
    readonly_fields = ('calculated_at',)


@admin.register(MatchInterest)
class MatchInterestAdmin(admin.ModelAdmin):
    list_display = ('user', 'target_user', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('user__email', 'target_user__email')


@admin.register(MatchRequest)
class MatchRequestAdmin(admin.ModelAdmin):
    list_display = ('requester', 'target', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('requester__email', 'target__email')
