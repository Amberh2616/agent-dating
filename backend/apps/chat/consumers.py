"""
Chat WebSocket consumers
聊天 WebSocket 消費者
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone


class ChatConsumer(AsyncWebsocketConsumer):
    """
    聊天 WebSocket 消費者
    Handles real-time chat messaging
    """

    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'chat_{self.conversation_id}'
        self.user = self.scope['user']

        # 檢查用戶是否有權訪問此對話
        if not await self.has_access():
            await self.close()
            return

        # 加入對話群組
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # 離開對話群組
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """接收前端訊息"""
        data = json.loads(text_data)
        message_type = data.get('type', 'message')

        if message_type == 'message':
            await self.handle_message(data)
        elif message_type == 'typing':
            await self.handle_typing(data)
        elif message_type == 'read':
            await self.handle_read(data)

    async def handle_message(self, data):
        """處理新訊息"""
        content = data.get('content', '')
        if not content:
            return

        # 儲存訊息到資料庫
        message = await self.save_message(content)

        # 廣播訊息給所有連接的用戶
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': {
                    'id': str(message.id),
                    'content': message.content,
                    'sender_type': message.sender_type,
                    'sender_id': str(message.sender_user_id or message.sender_agent_id),
                    'created_at': message.created_at.isoformat(),
                    'is_ai_generated': message.is_ai_generated,
                }
            }
        )

        # 如果是和 AI 對話，觸發 AI 回覆
        if await self.should_trigger_ai_response():
            await self.trigger_ai_response()

    async def handle_typing(self, data):
        """處理正在輸入狀態"""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing_indicator',
                'user_id': str(self.user.id),
                'is_typing': data.get('is_typing', False)
            }
        )

    async def handle_read(self, data):
        """處理已讀狀態"""
        message_id = data.get('message_id')
        if message_id:
            await self.mark_as_read(message_id)

    async def chat_message(self, event):
        """發送聊天訊息到 WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message']
        }))

    async def typing_indicator(self, event):
        """發送正在輸入指示器"""
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'user_id': event['user_id'],
            'is_typing': event['is_typing']
        }))

    async def ai_response(self, event):
        """發送 AI 回覆"""
        await self.send(text_data=json.dumps({
            'type': 'ai_response',
            'message': event['message']
        }))

    @database_sync_to_async
    def has_access(self):
        """檢查用戶是否有權訪問此對話"""
        from .models import Conversation
        try:
            conv = Conversation.objects.get(id=self.conversation_id)
            return (
                conv.user_participant_id == self.user.id or
                conv.other_user_id == self.user.id or
                (conv.agent_participant and conv.agent_participant.user_id == self.user.id)
            )
        except Conversation.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, content):
        """儲存訊息到資料庫"""
        from .models import Conversation, Message
        conv = Conversation.objects.get(id=self.conversation_id)

        message = Message.objects.create(
            conversation=conv,
            sender_type='user',
            sender_user=self.user,
            content=content,
            is_ai_generated=False
        )
        return message

    @database_sync_to_async
    def should_trigger_ai_response(self):
        """判斷是否需要觸發 AI 回覆"""
        from .models import Conversation
        conv = Conversation.objects.get(id=self.conversation_id)
        return conv.conversation_type == 'user_to_agent'

    async def trigger_ai_response(self):
        """觸發 AI 回覆 (異步任務)"""
        from apps.agents.tasks import generate_agent_response
        # 使用 Celery 異步處理 AI 回覆
        generate_agent_response.delay(str(self.conversation_id))

    @database_sync_to_async
    def mark_as_read(self, message_id):
        """標記訊息為已讀"""
        from .models import Message
        Message.objects.filter(id=message_id).update(
            is_read=True,
            read_at=timezone.now()
        )
