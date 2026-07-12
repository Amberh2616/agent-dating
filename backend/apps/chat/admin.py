from django.contrib import admin
from .models import Conversation, Message, ChatContext


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation_type', 'is_active', 'created_at', 'last_message_at')
    list_filter = ('conversation_type', 'is_active')
    readonly_fields = ('created_at', 'last_message_at')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'sender_type', 'emotion', 'created_at')
    list_filter = ('sender_type', 'emotion')
    search_fields = ('content',)
    readonly_fields = ('created_at',)


@admin.register(ChatContext)
class ChatContextAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'updated_at')
    readonly_fields = ('updated_at',)
