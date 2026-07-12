"""
AI 分身 Celery 任務
Agent Celery Tasks

Enhanced for autonomous AI social system with:
- Full action execution (move, chat, wave, etc.)
- A* pathfinding integration
- AI-to-AI conversation system
- WebSocket broadcasting
- LLM cost control
"""

import logging
import random
from datetime import datetime, timedelta
from celery import shared_task
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone
from django.core.cache import cache

logger = logging.getLogger(__name__)

# Cost control settings
MAX_LLM_CALLS_PER_HOUR = 10
LLM_COOLDOWN_SECONDS = 30
AI_CONVERSATION_MAX_ROUNDS = 3


@shared_task
def generate_agent_response(conversation_id: str):
    """
    生成 AI 分身的回覆 (異步任務)

    Args:
        conversation_id: 對話 ID
    """
    from apps.chat.models import Conversation, Message
    from apps.relationships.models import Relationship
    from ai.agents.soul_agent import SoulAgent
    from .services.memory_service import memory_service

    try:
        conversation = Conversation.objects.get(id=conversation_id)
    except Conversation.DoesNotExist:
        return

    # 檢查聊天模式 - 用戶親自聊天時跳過 AI 回覆
    if conversation.mode == 'user':
        logger.info(f"Conversation {conversation_id} in user mode, skipping AI response")
        return

    # 檢查暫停模式
    if conversation.mode == 'paused':
        logger.info(f"Conversation {conversation_id} is paused, skipping AI response")
        return

    # 獲取 AI 分身
    agent = conversation.other_agent
    if not agent:
        return

    # 獲取靈魂檔案
    try:
        soul_profile = agent.user.soul_profile
        soul_data = {
            'worldview': soul_profile.worldview,
            'lifeview': soul_profile.lifeview,
            'values': soul_profile.values,
            'interests': soul_profile.interests,
            'personality': soul_profile.personality,
            'communication_style': soul_profile.communication_style,
            'emotional_needs': soul_profile.emotional_needs,
            'love_style': soul_profile.love_style,
        }
    except Exception:
        soul_data = {}

    # 創建 Soul Agent
    soul_agent = SoulAgent(
        agent_data={'id': str(agent.id), 'name': agent.name},
        soul_profile=soul_data
    )

    # 獲取對話用戶
    user = conversation.user_participant
    if not user:
        return

    # 獲取關係數據
    try:
        relationship = Relationship.objects.get(
            user_a=min(user, agent.user, key=lambda u: u.id),
            user_b=max(user, agent.user, key=lambda u: u.id)
        )
        relationship_data = {
            'stage': relationship.stage,
            'closeness': relationship.closeness,
            'romantic': relationship.romantic,
        }
    except Relationship.DoesNotExist:
        relationship_data = {
            'stage': 'stranger',
            'closeness': 0,
            'romantic': 0,
        }

    # 獲取最後一條用戶訊息
    last_message = conversation.messages.filter(
        sender_type='user'
    ).order_by('-created_at').first()

    if not last_message:
        return

    # 獲取對話上下文
    recent_messages = conversation.messages.order_by('-created_at')[:10]
    context = [
        {
            'sender_type': msg.sender_type,
            'content': msg.content,
        }
        for msg in reversed(recent_messages)
    ]

    # 獲取與對方相關的記憶
    try:
        memories = memory_service.get_by_agent(
            agent_id=str(agent.id),
            related_agent_id=str(user.agent.id) if hasattr(user, 'agent') else '',
            limit=10
        )
        # 同時獲取重要記憶
        important_memories = memory_service.get_important(
            agent_id=str(agent.id),
            min_importance=7,
            limit=5
        )
        # 合併並去重
        memory_ids = {m['id'] for m in memories}
        for m in important_memories:
            if m['id'] not in memory_ids:
                memories.append(m)
        logger.info(f"Retrieved {len(memories)} memories for {agent.name}")
    except Exception as e:
        logger.warning(f"Failed to retrieve memories: {e}")
        memories = []

    # 獲取情緒描述
    emotion_description = agent.get_emotion_description()
    logger.info(f"Agent {agent.name} emotion: {emotion_description}")

    # 獲取最近的反思
    try:
        from .services.reflection_service import reflection_service
        reflections = reflection_service.get_recent_insights(
            agent_id=str(agent.id),
            hours=48,
            limit=5
        )
        logger.info(f"Retrieved {len(reflections)} reflections for {agent.name}")
    except Exception as e:
        logger.warning(f"Failed to retrieve reflections: {e}")
        reflections = []

    # 生成回覆 (需要異步轉同步)
    async def generate():
        return await soul_agent.generate_response(
            message=last_message.content,
            other_agent_data={
                'name': user.username,
                'preferred_language': 'English',  # 強制使用英文回覆
            },
            relationship_data=relationship_data,
            conversation_context=context,
            memories=memories,
            emotion_description=emotion_description,
            reflections=reflections
        )

    response_text = async_to_sync(generate)()

    # 儲存回覆
    message = Message.objects.create(
        conversation=conversation,
        sender_type='agent',
        sender_agent=agent,
        content=response_text,
        is_ai_generated=True
    )

    # 更新 Agent 的 last_chat_message (供前端輪詢顯示氣泡)
    from django.utils import timezone
    agent.last_chat_message = response_text[:500]  # 限制長度
    agent.last_chat_time = timezone.now()
    agent.save(update_fields=['last_chat_message', 'last_chat_time'])
    logger.info(f"Updated {agent.name} last_chat_message: {response_text[:50]}...")

    # 廣播氣泡到 World WebSocket (如果 Agent 在房間中)
    try:
        from apps.world.models import AgentPosition
        from apps.world.utils import broadcast_agent_chat
        position = AgentPosition.objects.filter(agent=agent).first()
        if position and position.room:
            broadcast_agent_chat(str(position.room.id), str(agent.id), response_text[:500], duration=8000)
            logger.info(f"Broadcast chat bubble for {agent.name} in room {position.room.name}")
    except Exception as e:
        logger.warning(f"Failed to broadcast chat bubble: {e}")

    # 通過 WebSocket 發送到聊天頻道
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'chat_{conversation_id}',
        {
            'type': 'ai_response',
            'message': {
                'id': str(message.id),
                'content': message.content,
                'sender_type': 'agent',
                'sender_id': str(agent.id),
                'created_at': message.created_at.isoformat(),
                'is_ai_generated': True,
            }
        }
    )

    # 更新關係 (互動計數)
    try:
        relationship.interaction_count += 1
        relationship.ai_interaction_count += 1
        # 簡單增加親密度
        if relationship.closeness < 100:
            relationship.closeness = min(100, relationship.closeness + 1)
        relationship.update_stage()
    except Exception:
        pass

    # 更新情緒 (對話後心情變好)
    try:
        agent.update_emotion({
            'happiness': 5,   # 聊天讓心情變好
            'energy': -3,     # 消耗一點精力
            'openness': 3     # 更願意交流
        })
        logger.info(f"Updated {agent.name} emotion after chat")
    except Exception as e:
        logger.warning(f"Failed to update emotion: {e}")


@shared_task
def run_agent_simulation():
    """
    執行 AI 分身模擬 (定期任務)
    讓所有在線的 AI 分身自主行動

    建議使用 APScheduler 每 5 秒調用一次
    """
    from .models import Agent

    online_agents = Agent.objects.filter(is_online=True, is_autonomous=True)
    logger.info(f"Running simulation for {online_agents.count()} agents")

    for agent in online_agents:
        # 分散執行避免併發
        process_agent_tick.delay(str(agent.id))


@shared_task(bind=True, max_retries=1)
def process_agent_tick(self, agent_id: str):
    """
    處理單個 AI 分身的 tick - Generative Agents 版本

    流程 (基於 Stanford Generative Agents):
    1. 感知環境 (Perception)
    2. 記憶檢索 (Memory Retrieval)
    3. 意圖管理 (Intent Check/Create)
    4. 決策行動 (Decision)
    5. 執行行動 (Execute)
    6. 廣播到 WebSocket

    Args:
        agent_id: Agent ID
    """
    from .models import Agent, Memory, AgentAction, AgentIntent
    from .services.memory_service import memory_service
    from .services.intent_service import intent_service
    from apps.world.models import AgentPosition, Room
    from apps.world.pathfinding import find_path_in_room
    from apps.world.utils import (
        broadcast_agent_path, broadcast_agent_chat,
        broadcast_agent_action, broadcast_agent_emotion,
        update_agent_position_in_db, get_nearby_agents,
        broadcast_proximity_event, broadcast_goal_achieved,
        log_interaction, get_recent_events
    )

    try:
        agent = Agent.objects.select_related('user').get(id=agent_id)
    except Agent.DoesNotExist:
        logger.warning(f"Agent {agent_id} not found")
        return

    # 檢查 Agent 是否正在忙碌 (移動中或對話中)
    if agent.current_action in ['walking', 'talking']:
        logger.debug(f"Agent {agent.name} is busy: {agent.current_action}")
        return

    # 獲取位置
    try:
        position = AgentPosition.objects.select_related('room').get(agent=agent)
        room = position.room
        if not room:
            logger.warning(f"Agent {agent.name} has no room")
            return
        room_id = str(room.id)
    except AgentPosition.DoesNotExist:
        logger.warning(f"Agent {agent.name} has no position")
        return

    # === 1. PERCEPTION - 感知環境 ===
    nearby_agents = get_nearby_agents(str(agent.id), room_id, radius=8)
    recent_events = get_recent_events(room_id, limit=5)

    # 計算時段
    hour = datetime.now().hour
    if 6 <= hour < 12:
        time_of_day = 'morning'
    elif 12 <= hour < 18:
        time_of_day = 'afternoon'
    elif 18 <= hour < 22:
        time_of_day = 'evening'
    else:
        time_of_day = 'night'

    perception = {
        'nearby_agents': nearby_agents,
        'recent_events': recent_events,
        'location': {
            'room_id': room_id,
            'room_type': room.room_type,
            'room_name': room.name,
            'x': position.x,
            'y': position.y,
        },
        'time_of_day': time_of_day,
    }

    # === 2. MEMORY RETRIEVAL - 記憶檢索 ===
    memories = memory_service.retrieve_for_decision(str(agent.id), perception)

    # === 3. INTENT MANAGEMENT - 意圖管理 ===
    intent = intent_service.get_active_intent(str(agent.id))

    # 如果沒有意圖或意圖過期，創建新意圖
    if not intent or (hasattr(intent, 'is_expired') and intent.is_expired):
        # 根據感知和記憶創建簡單意圖
        intent = _generate_reactive_intent(agent, perception, memories)

    # 激活意圖 (如果還是 pending)
    if intent and intent.status == 'pending':
        intent_service.activate_intent(str(intent.id))

    # === 4. DECISION - 決策行動 ===
    if intent:
        # 根據意圖獲取建議行動
        action = intent_service.get_suggested_action(intent, perception)
        logger.debug(f"Agent {agent.name} intent: {intent.goal}, step: {intent.current_step_name}, action: {action['type']}")
    else:
        # 沒有意圖時，使用 rule-based 決策
        action = _decide_fallback_action(agent, perception, memories)

    logger.info(f"Agent {agent.name} decided: {action['type']}")

    # === 5. EXECUTE - 執行行動 ===
    action_result = _execute_action(agent, action, perception, room, position, intent)

    # 推進意圖 (如果行動成功)
    if intent and action_result.get('success'):
        result = intent_service.advance_intent(
            str(intent.id),
            note=f"Executed {action['type']}"
        )
        if result.get('completed'):
            # 廣播目標達成
            broadcast_goal_achieved(room_id, str(agent.id), intent.goal, intent.goal_type)
            log_interaction(room_id, str(agent.id), 'goal_achieved', payload={'goal': intent.goal})


def _generate_reactive_intent(agent, perception, memories) -> 'AgentIntent':
    """
    根據感知生成反應式意圖
    Generate a reactive intent based on perception

    This is a simplified version that creates intents without LLM calls
    """
    from .models import AgentIntent
    from django.utils import timezone
    from datetime import timedelta

    nearby = perception.get('nearby_agents', [])
    time_of_day = perception.get('time_of_day', 'afternoon')

    # 決定目標類型
    if nearby and random.random() < 0.6:
        # 60% 機率社交
        target = random.choice(nearby)
        goal_type = random.choice(['make_friend', 'chat_topic', 'socialize'])
        goal = f"與 {target['name']} 聊聊天" if goal_type == 'chat_topic' else f"認識 {target['name']}"
        target_agent_id = target['id']
    elif time_of_day == 'night' or random.random() < 0.2:
        # 夜晚或 20% 機率休息
        goal_type = 'rest'
        goal = '找個地方休息一下'
        target_agent_id = None
    else:
        # 探索或觀察
        goal_type = random.choice(['explore_room', 'observe'])
        goal = '四處看看' if goal_type == 'explore_room' else '觀察周圍'
        target_agent_id = None

    # 步驟定義
    goal_steps = {
        'make_friend': ['find_target', 'approach', 'greet', 'exchange_intro', 'set_followup'],
        'chat_topic': ['find_interested', 'approach', 'start_topic', 'discuss'],
        'explore_room': ['look_around', 'move_random', 'observe_agents'],
        'rest': ['find_seat', 'sit', 'observe'],
        'observe': ['find_spot', 'watch'],
        'socialize': ['scan_room', 'choose_group', 'join_chat'],
    }

    intent = AgentIntent.objects.create(
        agent=agent,
        goal=goal,
        goal_type=goal_type,
        target_agent_id=target_agent_id if target_agent_id else None,
        status='pending',
        priority=random.randint(4, 7),
        steps=goal_steps.get(goal_type, ['observe']),
        expires_at=timezone.now() + timedelta(minutes=random.randint(15, 45))
    )

    return intent


def _decide_fallback_action(agent, perception, memories) -> dict:
    """
    備用決策邏輯 (無意圖時使用)
    Fallback decision logic when no intent is active
    """
    nearby = perception.get('nearby_agents', [])

    # 簡單 rule-based 決策
    if nearby and random.random() < 0.4:
        target = random.choice(nearby)
        if random.random() < 0.5:
            return {'type': 'wave', 'target': target['id']}
        else:
            return {'type': 'approach', 'target': target['id']}
    elif random.random() < 0.3:
        return {'type': 'observe', 'parameters': {}}
    else:
        return {'type': 'wander', 'parameters': {}}


def _execute_action(agent, action, perception, room, position, intent) -> dict:
    """
    執行行動並返回結果
    Execute action and return result
    """
    from .models import Memory
    from apps.world.pathfinding import find_path_in_room
    from apps.world.utils import (
        broadcast_agent_path, broadcast_agent_chat,
        broadcast_agent_action, broadcast_agent_emotion,
        update_agent_position_in_db, broadcast_proximity_event,
        log_interaction
    )

    room_id = str(room.id)
    action_type = action.get('type', 'idle')
    target_id = action.get('target')
    nearby_agents = perception.get('nearby_agents', [])

    if action_type == 'chat' and target_id:
        # 發起 AI-to-AI 對話
        cache_key = f"agent_chat_cooldown_{agent.id}"
        if cache.get(cache_key):
            logger.debug(f"Agent {agent.name} is on chat cooldown")
            return {'success': False, 'reason': 'cooldown'}

        # 設置冷卻
        cache.set(cache_key, True, LLM_COOLDOWN_SECONDS)

        # 更新狀態
        agent.current_action = 'talking'
        agent.current_target = target_id
        agent.save(update_fields=['current_action', 'current_target'])

        # 廣播互動開始
        broadcast_agent_action(room_id, str(agent.id), 'wave')
        log_interaction(room_id, str(agent.id), 'chat_message', target_id, x=position.x, y=position.y)

        # 發起對話任務
        run_ai_to_ai_conversation.delay(str(agent.id), target_id, room_id)
        return {'success': True, 'action': 'chat_started'}

    elif action_type == 'wave' and target_id:
        # 打招呼動作
        broadcast_agent_action(room_id, str(agent.id), 'wave')
        agent.current_emotion = 'happy'
        agent.save(update_fields=['current_emotion'])
        broadcast_agent_emotion(room_id, str(agent.id), 'happy')

        # 記錄交互
        log_interaction(room_id, str(agent.id), 'wave', target_id, x=position.x, y=position.y)

        # 創建記憶
        target_name = next((a['name'] for a in nearby_agents if a['id'] == target_id), 'someone')
        Memory.objects.create(
            agent=agent,
            type='observation',
            content=f"向 {target_name} 打了招呼",
            importance=3,
            related_agents=[target_id],
            location={'room_id': room_id, 'x': position.x, 'y': position.y},
            emotion='happy'
        )
        return {'success': True, 'action': 'wave'}

    elif action_type in ['move', 'wander', 'approach', 'move_to_agent']:
        # 移動行動
        if action_type == 'wander':
            target_x = random.randint(max(0, position.x - 5), min(room.width - 1, position.x + 5))
            target_y = random.randint(max(0, position.y - 5), min(room.height - 1, position.y + 5))
        elif action_type in ['approach', 'move_to_agent'] and target_id:
            # 找到目標位置
            target_agent = next((a for a in nearby_agents if a['id'] == target_id), None)
            if target_agent:
                # 移動到目標附近 (不是完全重疊)
                target_x = target_agent['x'] + random.choice([-1, 0, 1])
                target_y = target_agent['y'] + random.choice([-1, 0, 1])
                target_x = max(0, min(room.width - 1, target_x))
                target_y = max(0, min(room.height - 1, target_y))
            else:
                target_x = position.x
                target_y = position.y
        else:
            target_x = action.get('parameters', {}).get('x', position.x)
            target_y = action.get('parameters', {}).get('y', position.y)

        # 使用 A* 計算路徑
        start = (position.x, position.y)
        goal = (target_x, target_y)

        if start != goal:
            path = find_path_in_room(room, start, goal, exclude_agent_id=str(agent.id))

            if path and len(path) > 1:
                agent.current_action = 'walking'
                agent.save(update_fields=['current_action'])

                broadcast_agent_path(room_id, str(agent.id), path, speed=200)

                final_pos = path[-1]
                update_agent_position_in_db(str(agent.id), final_pos['x'], final_pos['y'], final_pos['direction'])

                # 如果靠近目標，廣播 proximity 事件
                if target_id:
                    broadcast_proximity_event(room_id, str(agent.id), target_id, 1)
                    log_interaction(room_id, str(agent.id), 'proximity', target_id, x=final_pos['x'], y=final_pos['y'])

                move_duration = len(path) * 0.2
                reset_agent_action.apply_async(args=[str(agent.id)], countdown=move_duration)
                return {'success': True, 'action': 'move'}

        return {'success': False, 'reason': 'no_path'}

    elif action_type == 'sit':
        broadcast_agent_action(room_id, str(agent.id), 'sit')
        agent.current_action = 'sitting'
        agent.save(update_fields=['current_action'])
        return {'success': True, 'action': 'sit'}

    elif action_type == 'dance':
        broadcast_agent_action(room_id, str(agent.id), 'dance')
        agent.current_action = 'dancing'
        agent.save(update_fields=['current_action'])
        reset_agent_action.apply_async(args=[str(agent.id)], countdown=5)
        return {'success': True, 'action': 'dance'}

    elif action_type == 'observe':
        agent.current_emotion = 'thinking'
        agent.save(update_fields=['current_emotion'])
        broadcast_agent_emotion(room_id, str(agent.id), 'thinking')
        return {'success': True, 'action': 'observe'}

    else:
        # idle
        if agent.current_action != 'idle':
            agent.current_action = 'idle'
            agent.save(update_fields=['current_action'])
        return {'success': True, 'action': 'idle'}


@shared_task
def reset_agent_action(agent_id: str):
    """重置 Agent 動作狀態為 idle"""
    from .models import Agent

    try:
        Agent.objects.filter(id=agent_id).update(
            current_action='idle',
            current_target=None
        )
    except Exception as e:
        logger.error(f"Error resetting agent action: {e}")


@shared_task
def initiate_conversation(agent_id: str, target_agent_id: str):
    """
    發起 AI 間的對話

    Args:
        agent_id: 發起方 Agent ID
        target_agent_id: 目標 Agent ID
    """
    from .models import Agent
    from apps.chat.models import Conversation, Message
    from ai.agents.soul_agent import SoulAgent

    try:
        agent = Agent.objects.get(id=agent_id)
        target = Agent.objects.get(id=target_agent_id)
    except Agent.DoesNotExist:
        return

    # 檢查是否已有對話
    existing = Conversation.objects.filter(
        conversation_type='agent_to_agent',
        agent_participant=agent,
        other_agent=target
    ).first()

    if not existing:
        # 創建新對話
        conversation = Conversation.objects.create(
            conversation_type='agent_to_agent',
            agent_participant=agent,
            other_agent=target
        )
    else:
        conversation = existing

    # 生成打招呼訊息
    try:
        soul_profile = agent.user.soul_profile
        soul_data = {
            'interests': soul_profile.interests,
            'personality': soul_profile.personality,
            'communication_style': soul_profile.communication_style,
        }
    except Exception:
        soul_data = {}

    try:
        target_soul = target.user.soul_profile
        target_soul_data = {
            'interests': target_soul.interests,
        }
    except Exception:
        target_soul_data = {}

    soul_agent = SoulAgent(
        agent_data={'id': str(agent.id), 'name': agent.name},
        soul_profile=soul_data
    )

    # 取得目標用戶的語言偏好
    target_language = target.user.preferred_language if target.user else 'zh-hant'

    async def generate_greeting():
        return await soul_agent.generate_first_message(
            {
                'id': str(target.id),
                'name': target.name,
                'preferred_language': target_language,
            },
            target_soul_data
        )

    greeting = async_to_sync(generate_greeting)()

    # 儲存訊息
    Message.objects.create(
        conversation=conversation,
        sender_type='agent',
        sender_agent=agent,
        content=greeting,
        is_ai_generated=True
    )

    # 更新 agent 統計
    agent.total_conversations += 1
    agent.save()


@shared_task(bind=True, max_retries=0)
def run_ai_to_ai_conversation(self, agent_id: str, target_agent_id: str, room_id: str):
    """
    執行 AI-to-AI 對話

    特點:
    - 2-4 輪對話
    - 每輪間隔 2 秒
    - 更新記憶和關係
    - 廣播對話氣泡到房間
    - 硬限制防止無限循環

    Args:
        agent_id: 發起方 Agent ID
        target_agent_id: 目標 Agent ID
        room_id: 房間 ID
    """
    import time
    from .models import Agent, Memory
    from .services.memory_service import memory_service
    from apps.chat.models import Conversation, Message
    from apps.relationships.models import Relationship
    from apps.world.utils import broadcast_agent_chat, broadcast_agent_emotion
    from ai.agents.soul_agent import SoulAgent

    logger.info(f"Starting AI-to-AI conversation: {agent_id} -> {target_agent_id}")

    try:
        agent = Agent.objects.select_related('user').get(id=agent_id)
        target = Agent.objects.select_related('user').get(id=target_agent_id)
    except Agent.DoesNotExist:
        logger.error("Agent not found for AI-to-AI conversation")
        return

    # 獲取或創建對話
    conversation = Conversation.objects.filter(
        conversation_type='agent_to_agent',
        agent_participant=agent,
        other_agent=target
    ).first()

    if not conversation:
        conversation = Conversation.objects.create(
            conversation_type='agent_to_agent',
            agent_participant=agent,
            other_agent=target
        )

    # 獲取靈魂檔案
    def get_soul_data(ag):
        try:
            sp = ag.user.soul_profile
            return {
                'worldview': sp.worldview,
                'interests': sp.interests,
                'personality': sp.personality,
                'communication_style': sp.communication_style,
            }
        except Exception:
            return {}

    agent_soul = get_soul_data(agent)
    target_soul = get_soul_data(target)

    # 獲取關係
    try:
        relationship = Relationship.objects.get(
            user_a=min(agent.user, target.user, key=lambda u: u.id),
            user_b=max(agent.user, target.user, key=lambda u: u.id)
        )
        relationship_data = {
            'stage': relationship.stage,
            'closeness': relationship.closeness,
        }
    except Relationship.DoesNotExist:
        relationship = None
        relationship_data = {'stage': 'stranger', 'closeness': 0}

    # 決定對話輪數 (2-3 輪，根據親密度)
    num_rounds = 2 if relationship_data['closeness'] < 30 else 3

    # 對話歷史
    context = []

    # 創建 SoulAgent 實例
    agent_soul_agent = SoulAgent(
        agent_data={'id': str(agent.id), 'name': agent.name},
        soul_profile=agent_soul
    )
    target_soul_agent = SoulAgent(
        agent_data={'id': str(target.id), 'name': target.name},
        soul_profile=target_soul
    )

    # 語言偏好
    agent_lang = agent.user.preferred_language if agent.user else 'zh-hant'
    target_lang = target.user.preferred_language if target.user else 'zh-hant'

    # 獲取雙方對彼此的記憶
    try:
        agent_memories = memory_service.get_by_agent(agent_id, target_agent_id, limit=10)
        target_memories = memory_service.get_by_agent(target_agent_id, agent_id, limit=10)
        logger.info(f"Retrieved memories: {agent.name}={len(agent_memories)}, {target.name}={len(target_memories)}")
    except Exception as e:
        logger.warning(f"Failed to retrieve memories for AI-to-AI: {e}")
        agent_memories = []
        target_memories = []

    # 獲取雙方情緒描述
    agent_emotion = agent.get_emotion_description()
    target_emotion = target.get_emotion_description()
    logger.info(f"Emotions: {agent.name}={agent_emotion}, {target.name}={target_emotion}")

    # 獲取雙方反思
    try:
        from .services.reflection_service import reflection_service
        agent_reflections = reflection_service.get_recent_insights(str(agent.id), hours=48, limit=3)
        target_reflections = reflection_service.get_recent_insights(str(target.id), hours=48, limit=3)
        logger.info(f"Reflections: {agent.name}={len(agent_reflections)}, {target.name}={len(target_reflections)}")
    except Exception as e:
        logger.warning(f"Failed to retrieve reflections for AI-to-AI: {e}")
        agent_reflections = []
        target_reflections = []

    try:
        for round_num in range(num_rounds):
            logger.debug(f"AI conversation round {round_num + 1}/{num_rounds}")

            # === Agent 說話 ===
            if round_num == 0:
                # 第一輪：打招呼
                async def generate_greeting():
                    return await agent_soul_agent.generate_first_message(
                        {'id': str(target.id), 'name': target.name, 'preferred_language': target_lang},
                        target_soul
                    )
                agent_message = async_to_sync(generate_greeting)()
            else:
                # 後續輪：回應
                async def generate_response():
                    return await agent_soul_agent.generate_response(
                        message=context[-1]['content'] if context else '',
                        other_agent_data={'name': target.name, 'preferred_language': target_lang},
                        relationship_data=relationship_data,
                        conversation_context=context,
                        memories=agent_memories,
                        emotion_description=agent_emotion,
                        reflections=agent_reflections
                    )
                agent_message = async_to_sync(generate_response)()

            # 儲存並廣播
            msg = Message.objects.create(
                conversation=conversation,
                sender_type='agent',
                sender_agent=agent,
                content=agent_message,
                is_ai_generated=True
            )
            context.append({'sender_type': 'agent', 'sender_name': agent.name, 'content': agent_message})

            # 更新 Agent 的 last_chat_message (供前端輪詢顯示)
            agent.last_chat_message = agent_message
            agent.last_chat_time = timezone.now()
            agent.save(update_fields=['last_chat_message', 'last_chat_time'])

            # 廣播對話氣泡
            broadcast_agent_chat(room_id, str(agent.id), agent_message, duration=4000)
            logger.debug(f"{agent.name}: {agent_message[:50]}...")

            # 等待 10 秒
            time.sleep(10)

            # === Target 回覆 ===
            async def generate_target_response():
                return await target_soul_agent.generate_response(
                    message=agent_message,
                    other_agent_data={'name': agent.name, 'preferred_language': agent_lang},
                    relationship_data=relationship_data,
                    conversation_context=context,
                    memories=target_memories,
                    emotion_description=target_emotion,
                    reflections=target_reflections
                )
            target_message = async_to_sync(generate_target_response)()

            # 儲存並廣播
            msg = Message.objects.create(
                conversation=conversation,
                sender_type='agent',
                sender_agent=target,
                content=target_message,
                is_ai_generated=True
            )
            context.append({'sender_type': 'agent', 'sender_name': target.name, 'content': target_message})

            # 更新 Target 的 last_chat_message (供前端輪詢顯示)
            target.last_chat_message = target_message
            target.last_chat_time = timezone.now()
            target.save(update_fields=['last_chat_message', 'last_chat_time'])

            # 廣播對話氣泡
            broadcast_agent_chat(room_id, str(target.id), target_message, duration=4000)
            logger.debug(f"{target.name}: {target_message[:50]}...")

            # 等待 10 秒 (除了最後一輪)
            if round_num < num_rounds - 1:
                time.sleep(10)

        # === 對話結束處理 ===

        # 更新情緒
        broadcast_agent_emotion(room_id, str(agent.id), 'happy')
        broadcast_agent_emotion(room_id, str(target.id), 'happy')

        # 創建記憶 - 包含對話摘要
        # 提取對話中的關鍵內容
        conversation_summary = " / ".join([
            msg.get('content', '')[:50] for msg in context[:3]
        ])

        Memory.objects.create(
            agent=agent,
            type='conversation',
            content=f"和 {target.name} 聊天：{conversation_summary}",
            importance=6,
            related_agents=[str(target.id)],
            location={'room_id': room_id},
            emotion='happy'
        )
        Memory.objects.create(
            agent=target,
            type='conversation',
            content=f"和 {agent.name} 聊天：{conversation_summary}",
            importance=6,
            related_agents=[str(agent.id)],
            location={'room_id': room_id},
            emotion='happy'
        )

        # 更新關係
        if relationship:
            relationship.interaction_count += 1
            relationship.ai_interaction_count += 1
            if relationship.closeness < 100:
                relationship.closeness = min(100, relationship.closeness + 2)
            relationship.update_stage()

        # 更新 Agent 統計
        agent.total_conversations += 1
        target.total_conversations += 1
        agent.save(update_fields=['total_conversations'])
        target.save(update_fields=['total_conversations'])

        # 更新雙方情緒 (愉快的對話)
        try:
            agent.update_emotion({
                'happiness': 8,
                'energy': -5,
                'openness': 5,
                'stress': -3
            })
            target.update_emotion({
                'happiness': 8,
                'energy': -5,
                'openness': 5,
                'stress': -3
            })
            logger.info(f"Updated emotions after AI-to-AI conversation")
        except Exception as e:
            logger.warning(f"Failed to update emotions: {e}")

        # 生成對話摘要
        generate_conversation_summary.delay(
            str(conversation.id),
            context,
            str(agent.id),
            str(target.id)
        )

        # 檢查是否需要生成反思 (每 5 次對話後)
        if agent.total_conversations % 5 == 0:
            generate_agent_reflections.delay(str(agent.id))
            logger.info(f"Triggered reflection generation for {agent.name}")
        if target.total_conversations % 5 == 0:
            generate_agent_reflections.delay(str(target.id))
            logger.info(f"Triggered reflection generation for {target.name}")

        logger.info(f"AI-to-AI conversation completed: {agent.name} <-> {target.name}")

    except Exception as e:
        logger.error(f"Error in AI-to-AI conversation: {e}")

    finally:
        # 重置 Agent 狀態
        Agent.objects.filter(id__in=[agent_id, target_agent_id]).update(
            current_action='idle',
            current_target=None
        )


@shared_task
def generate_conversation_summary(conversation_id: str, context: list, agent_id: str, target_id: str):
    """
    生成對話摘要
    Generate conversation summary after AI-to-AI chat

    Args:
        conversation_id: Conversation ID
        context: List of message dicts with sender_name and content
        agent_id: Initiating agent ID
        target_id: Target agent ID
    """
    import json
    from .models import Agent
    from apps.chat.models import Conversation, ConversationSummary, Message
    from ai.prompts.summary import get_summary_prompt

    logger.info(f"Generating summary for conversation {conversation_id}")

    try:
        conversation = Conversation.objects.get(id=conversation_id)
        agent = Agent.objects.select_related('user').get(id=agent_id)
        target = Agent.objects.select_related('user').get(id=target_id)
    except (Conversation.DoesNotExist, Agent.DoesNotExist) as e:
        logger.error(f"Error loading data for summary: {e}")
        return

    # 獲取最近的摘要以取得之前的印象分
    last_summary = ConversationSummary.objects.filter(
        conversation=conversation
    ).order_by('-created_at').first()
    previous_score = last_summary.impression_score if last_summary else 50

    # 獲取語言偏好
    owner_lang = agent.user.preferred_language if agent.user else 'zh-hant'

    # 格式化對話內容
    messages_text = "\n".join([
        f"{msg.get('sender_name', 'Unknown')}: {msg.get('content', '')}"
        for msg in context
    ])

    # 構建提示語
    prompt_template = get_summary_prompt(owner_lang)
    prompt = prompt_template.format(
        agent_name=agent.name,
        owner_name=agent.user.username if agent.user else 'User',
        other_agent_name=target.name,
        other_owner_name=target.user.username if target.user else 'User',
        conversation_messages=messages_text,
        previous_impression_score=previous_score
    )

    # 使用 LLM 生成摘要
    try:
        from ai.llm import LLMService
        llm_service = LLMService()

        async def generate():
            messages = [
                {"role": "system", "content": "You are an AI assistant that analyzes conversations and generates structured summaries in JSON format."},
                {"role": "user", "content": prompt}
            ]
            return await llm_service.generate_response(
                messages=messages,
                max_tokens=500,
                temperature=0.3
            )

        response_text = async_to_sync(generate)()

        # 解析 JSON
        # 處理可能的 markdown 代碼塊
        json_text = response_text
        if '```json' in json_text:
            json_text = json_text.split('```json')[1].split('```')[0]
        elif '```' in json_text:
            json_text = json_text.split('```')[1].split('```')[0]

        result = json.loads(json_text.strip())

        # 計算新的印象分
        delta = max(-10, min(10, result.get('impression_delta', 0)))
        new_score = max(0, min(100, previous_score + delta))

        # 決定趨勢
        if delta > 2:
            trend = 'up'
        elif delta < -2:
            trend = 'down'
        else:
            trend = 'neutral'

        # 獲取對話時間範圍
        messages = Message.objects.filter(
            conversation=conversation
        ).order_by('created_at')

        first_msg = messages.first()
        last_msg = messages.last()

        # 創建摘要
        summary = ConversationSummary.objects.create(
            conversation=conversation,
            period_start=first_msg.created_at if first_msg else timezone.now(),
            period_end=last_msg.created_at if last_msg else timezone.now(),
            message_count=len(context),
            summary_text=result.get('summary', '對話已完成'),
            key_topics=result.get('topics', []),
            emotional_tone=result.get('tone', 'neutral'),
            best_moment=result.get('best_moment', ''),
            shared_interests_found=result.get('shared_interests', []),
            impression_score=new_score,
            impression_delta=delta,
            compatibility_trend=trend,
        )

        logger.info(f"Summary created for conversation {conversation_id}: score {new_score} (delta {delta:+d})")

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse summary JSON: {e}")
        # 創建基本摘要
        ConversationSummary.objects.create(
            conversation=conversation,
            period_start=timezone.now(),
            period_end=timezone.now(),
            message_count=len(context),
            summary_text='AI 代聊已完成',
            impression_score=previous_score,
            impression_delta=0,
            compatibility_trend='neutral',
        )

    except Exception as e:
        logger.error(f"Error generating summary: {e}")


@shared_task
def generate_agent_reflections(agent_id: str = None):
    """
    生成 AI 反思
    Generate reflections for agents based on recent memories

    Args:
        agent_id: 特定 Agent ID，如果為 None 則處理所有符合條件的 Agent
    """
    from .models import Agent
    from .services.reflection_service import reflection_service

    if agent_id:
        # 處理特定 Agent
        agents = Agent.objects.filter(id=agent_id)
    else:
        # 處理所有在線的 Agent
        agents = Agent.objects.filter(is_online=True)

    reflections_generated = 0

    for agent in agents:
        try:
            # 檢查是否需要反思
            if not reflection_service.should_reflect(str(agent.id)):
                continue

            # 生成反思
            reflections = reflection_service.generate_reflection(
                agent_id=str(agent.id),
                memory_count=20,
                min_importance=4,
                language=agent.user.preferred_language if agent.user else 'zh-hant'
            )

            if reflections:
                reflections_generated += len(reflections)
                logger.info(f"Generated {len(reflections)} reflections for {agent.name}")

                # 根據反思更新情緒
                for r in reflections:
                    if r.importance >= 7:
                        # 重要的反思會影響情緒
                        agent.update_emotion({
                            'openness': 5,  # 反思後更開放
                            'stress': -5,   # 理清思緒減少壓力
                        })

        except Exception as e:
            logger.error(f"Error generating reflections for {agent.name}: {e}")

    logger.info(f"Total reflections generated: {reflections_generated}")
    return reflections_generated


@shared_task
def apply_personality_growth(agent_id: str):
    """
    根據反思和互動歷史，微調 AI 性格
    Apply personality growth based on reflections and interaction history

    這是長期學習機制，會根據：
    - 累積的反思洞察
    - 互動模式
    - 情緒歷史
    來微調 AI 的性格基準線
    """
    from .models import Agent, AgentReflection, Memory
    from .services.reflection_service import reflection_service

    try:
        agent = Agent.objects.select_related('user').get(id=agent_id)
    except Agent.DoesNotExist:
        logger.error(f"Agent {agent_id} not found")
        return

    # 獲取最近的反思
    recent_reflections = AgentReflection.objects.filter(
        agent_id=agent_id
    ).order_by('-created_at')[:10]

    if recent_reflections.count() < 3:
        logger.info(f"Not enough reflections for personality growth ({recent_reflections.count()} < 3)")
        return

    # 分析反思中的情緒傾向
    positive_keywords = ['開心', '喜歡', '有趣', 'happy', 'like', 'enjoy', 'fun', '愉快']
    negative_keywords = ['難過', '討厭', '無聊', 'sad', 'hate', 'boring', '失望']
    social_keywords = ['聊天', '朋友', '認識', 'chat', 'friend', 'meet', '交流']

    positive_count = 0
    negative_count = 0
    social_count = 0

    for r in recent_reflections:
        content = (r.summary + ' ' + r.insight).lower()
        for kw in positive_keywords:
            if kw in content:
                positive_count += 1
        for kw in negative_keywords:
            if kw in content:
                negative_count += 1
        for kw in social_keywords:
            if kw in content:
                social_count += 1

    # 根據分析微調情緒基準線
    baseline = agent.get_emotion_baseline()

    if positive_count > negative_count * 2:
        # 正面經驗多，提升 happiness 基準線
        baseline['happiness'] = min(70, baseline.get('happiness', 50) + 2)
        logger.info(f"{agent.name}: Positive experiences increased happiness baseline")

    if social_count > 5:
        # 社交活躍，提升 openness 基準線
        baseline['openness'] = min(70, baseline.get('openness', 50) + 2)
        logger.info(f"{agent.name}: Social activity increased openness baseline")

    if negative_count > positive_count:
        # 負面經驗多，可能變得更謹慎
        baseline['openness'] = max(30, baseline.get('openness', 50) - 1)
        baseline['stress'] = min(50, baseline.get('stress', 30) + 2)
        logger.info(f"{agent.name}: Negative experiences adjusted baseline")

    # 保存更新的基準線
    agent.emotion_baseline = baseline
    agent.save(update_fields=['emotion_baseline'])

    logger.info(f"Applied personality growth for {agent.name}: {baseline}")


@shared_task
def trigger_scheduled_ai_conversations():
    """
    定期觸發 AI 代聊
    Trigger scheduled AI-to-AI conversations

    建議每小時執行一次，選擇:
    - 高配對分 (>60%) 的配對
    - 6 小時內未聊天的配對
    - 聊天模式為 'ai' 的對話
    """
    from .models import Agent
    from apps.chat.models import Conversation
    from apps.matching.models import MatchScore
    from apps.world.models import Room, AgentPosition

    logger.info("Triggering scheduled AI conversations")

    # 獲取一個活躍房間
    room = Room.objects.filter(is_active=True).first()
    if not room:
        logger.warning("No active room found for AI conversations")
        return

    # 找出高配對分的配對 (match_score > 60)
    # 且最後聊天時間超過 6 小時
    cutoff_time = timezone.now() - timedelta(hours=6)

    high_matches = MatchScore.objects.filter(
        score__gte=60
    ).select_related('user_a', 'user_b').order_by('-score')[:10]

    conversations_triggered = 0

    for match in high_matches:
        try:
            # 獲取雙方的 Agent
            agent_a = Agent.objects.filter(user=match.user_a).first()
            agent_b = Agent.objects.filter(user=match.user_b).first()

            if not agent_a or not agent_b:
                continue

            # 檢查是否已有對話
            conversation = Conversation.objects.filter(
                conversation_type='agent_to_agent',
                agent_participant=agent_a,
                other_agent=agent_b
            ).first()

            # 跳過非 AI 模式的對話
            if conversation and conversation.mode != 'ai':
                continue

            # 檢查最後聊天時間
            if conversation and conversation.last_message_at:
                if conversation.last_message_at > cutoff_time:
                    continue  # 最近聊過了

            # 確保 Agent 在房間裡有位置
            for ag in [agent_a, agent_b]:
                pos, created = AgentPosition.objects.get_or_create(
                    agent=ag,
                    defaults={
                        'room': room,
                        'x': random.randint(2, 8),
                        'y': random.randint(2, 6),
                        'direction': 2
                    }
                )
                if not pos.room:
                    pos.room = room
                    pos.save()

            # 觸發 AI 對話
            run_ai_to_ai_conversation.delay(
                str(agent_a.id),
                str(agent_b.id),
                str(room.id)
            )

            conversations_triggered += 1
            logger.info(f"Triggered AI conversation: {agent_a.name} <-> {agent_b.name}")

            # 限制每次最多觸發 3 個對話
            if conversations_triggered >= 3:
                break

        except Exception as e:
            logger.error(f"Error triggering conversation for match: {e}")
            continue

    logger.info(f"Triggered {conversations_triggered} AI conversations")
