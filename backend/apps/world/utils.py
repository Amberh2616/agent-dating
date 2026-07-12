"""
World Utilities
虛擬世界工具函數

Functions for broadcasting events from Celery tasks to WebSocket clients
"""

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


def get_room_group_name(room_id: str) -> str:
    """獲取房間的 channel group 名稱"""
    return f'world_{room_id}'


def broadcast_to_room(room_id: str, event_type: str, data: dict):
    """
    廣播事件到房間內所有客戶端

    Args:
        room_id: 房間 ID
        event_type: 事件類型 (對應 consumer 的 handler 方法名)
        data: 事件數據
    """
    channel_layer = get_channel_layer()
    if not channel_layer:
        logger.warning("Channel layer not available")
        return

    group_name = get_room_group_name(room_id)

    try:
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': event_type,
                **data
            }
        )
    except Exception as e:
        logger.error(f"Failed to broadcast to room {room_id}: {e}")


def broadcast_agent_path(room_id: str, agent_id: str, path: List[Dict], speed: int = 200):
    """
    廣播 Agent 移動路徑

    Args:
        room_id: 房間 ID
        agent_id: Agent ID
        path: 路徑列表 [{"x": 0, "y": 0, "direction": 2}, ...]
        speed: 每格移動時間 (毫秒)
    """
    broadcast_to_room(room_id, 'agent_path_update', {
        'agent_id': agent_id,
        'path': path,
        'speed': speed,
    })


def broadcast_agent_chat(room_id: str, agent_id: str, message: str, duration: int = 5000):
    """
    廣播 Agent 對話氣泡

    Args:
        room_id: 房間 ID
        agent_id: Agent ID
        message: 訊息內容
        duration: 顯示時間 (毫秒)
    """
    broadcast_to_room(room_id, 'agent_chat_bubble', {
        'agent_id': agent_id,
        'message': message,
        'duration': duration,
    })


def broadcast_agent_action(room_id: str, agent_id: str, action: str):
    """
    廣播 Agent 動作

    Args:
        room_id: 房間 ID
        agent_id: Agent ID
        action: 動作類型 (wave, sit, stand, dance, think)
    """
    broadcast_to_room(room_id, 'agent_action_update', {
        'agent_id': agent_id,
        'action': action,
    })


def broadcast_agent_emotion(room_id: str, agent_id: str, emotion: str):
    """
    廣播 Agent 情緒變化

    Args:
        room_id: 房間 ID
        agent_id: Agent ID
        emotion: 情緒 (neutral, happy, sad, excited, thinking)
    """
    broadcast_to_room(room_id, 'agent_emotion_update', {
        'agent_id': agent_id,
        'emotion': emotion,
    })


def broadcast_agent_enter(room_id: str, agent_data: dict):
    """
    廣播 Agent 進入房間

    Args:
        room_id: 房間 ID
        agent_data: Agent 資料 {id, name, look, x, y, direction, action, emotion}
    """
    broadcast_to_room(room_id, 'agent_enter_room', {
        'agent': agent_data,
    })


def broadcast_agent_leave(room_id: str, agent_id: str):
    """
    廣播 Agent 離開房間

    Args:
        room_id: 房間 ID
        agent_id: Agent ID
    """
    broadcast_to_room(room_id, 'agent_leave_room', {
        'agent_id': agent_id,
    })


def broadcast_agent_position(room_id: str, agent_id: str, x: int, y: int, direction: int = 2):
    """
    廣播 Agent 位置更新 (瞬間移動)

    Args:
        room_id: 房間 ID
        agent_id: Agent ID
        x: X 座標
        y: Y 座標
        direction: 面向方向 (0-7)
    """
    broadcast_to_room(room_id, 'agent_position_update', {
        'agent_id': agent_id,
        'x': x,
        'y': y,
        'direction': direction,
    })


def broadcast_agent_interaction(
    room_id: str,
    initiator_id: str,
    target_id: str,
    interaction_type: str
):
    """
    廣播 Agent 互動事件

    Args:
        room_id: 房間 ID
        initiator_id: 發起者 Agent ID
        target_id: 目標 Agent ID
        interaction_type: 互動類型 (greet, talk, gift)
    """
    broadcast_to_room(room_id, 'agent_interaction', {
        'initiator_id': initiator_id,
        'target_id': target_id,
        'interaction_type': interaction_type,
    })


def update_agent_position_in_db(agent_id: str, x: int, y: int, direction: int = None):
    """
    更新 Agent 在資料庫中的位置

    Args:
        agent_id: Agent ID
        x: X 座標
        y: Y 座標
        direction: 面向方向 (可選)
    """
    from .models import AgentPosition

    update_fields = {'x': x, 'y': y, 'is_moving': False}
    if direction is not None:
        update_fields['direction'] = direction

    AgentPosition.objects.filter(agent_id=agent_id).update(**update_fields)


def get_agents_in_room(room_id: str) -> List[dict]:
    """
    獲取房間內所有 Agent

    Args:
        room_id: 房間 ID

    Returns:
        Agent 列表
    """
    from .models import AgentPosition

    positions = AgentPosition.objects.filter(
        room_id=room_id
    ).select_related('agent')

    agents = []
    for pos in positions:
        agents.append({
            'id': str(pos.agent.id),
            'name': pos.agent.name,
            'look': pos.agent.avatar_look,
            'x': pos.x,
            'y': pos.y,
            'direction': pos.direction,
            'action': pos.agent.current_action,
            'emotion': pos.agent.current_emotion,
            'is_autonomous': pos.agent.is_autonomous,
        })

    return agents


def get_nearby_agents(agent_id: str, room_id: str, radius: int = 5) -> List[dict]:
    """
    獲取附近的 Agent

    Args:
        agent_id: 當前 Agent ID
        room_id: 房間 ID
        radius: 檢測半徑

    Returns:
        附近 Agent 列表
    """
    from .models import AgentPosition

    try:
        my_position = AgentPosition.objects.get(agent_id=agent_id)
    except AgentPosition.DoesNotExist:
        return []

    nearby = []
    positions = AgentPosition.objects.filter(
        room_id=room_id
    ).exclude(agent_id=agent_id).select_related('agent')

    for pos in positions:
        distance = max(abs(pos.x - my_position.x), abs(pos.y - my_position.y))
        if distance <= radius:
            nearby.append({
                'id': str(pos.agent.id),
                'name': pos.agent.name,
                'x': pos.x,
                'y': pos.y,
                'distance': distance,
                'action': pos.agent.current_action,
                'emotion': pos.agent.current_emotion,
            })

    # 按距離排序
    nearby.sort(key=lambda a: a['distance'])
    return nearby


# === New Generative Agent Events ===

def broadcast_proximity_event(room_id: str, agent_id: str, target_id: str, distance: int):
    """
    廣播靠近事件
    Broadcast proximity event when agents get close

    Args:
        room_id: Room ID
        agent_id: Agent who approached
        target_id: Target agent
        distance: Distance between agents
    """
    broadcast_to_room(room_id, 'agent_proximity', {
        'agent_id': agent_id,
        'target_id': target_id,
        'distance': distance,
    })


def broadcast_invite_event(
    room_id: str,
    from_agent_id: str,
    to_agent_id: str,
    destination_room_id: str,
    destination_room_name: str
):
    """
    廣播邀請事件
    Broadcast invite event when an agent invites another

    Args:
        room_id: Current room ID
        from_agent_id: Inviting agent ID
        to_agent_id: Invited agent ID
        destination_room_id: Destination room ID
        destination_room_name: Destination room name
    """
    broadcast_to_room(room_id, 'agent_invite', {
        'from_agent_id': from_agent_id,
        'to_agent_id': to_agent_id,
        'destination_room_id': destination_room_id,
        'destination_room_name': destination_room_name,
    })


def broadcast_goal_achieved(room_id: str, agent_id: str, goal_description: str, goal_type: str):
    """
    廣播達成目標事件
    Broadcast goal achieved event

    Args:
        room_id: Room ID
        agent_id: Agent who achieved the goal
        goal_description: Description of the goal
        goal_type: Type of goal (make_friend, chat_topic, etc.)
    """
    broadcast_to_room(room_id, 'agent_goal_achieved', {
        'agent_id': agent_id,
        'goal_description': goal_description,
        'goal_type': goal_type,
    })


def broadcast_intent_update(room_id: str, agent_id: str, intent_data: dict):
    """
    廣播意圖更新
    Broadcast intent status update

    Args:
        room_id: Room ID
        agent_id: Agent ID
        intent_data: Intent information dict
    """
    broadcast_to_room(room_id, 'agent_intent_update', {
        'agent_id': agent_id,
        'intent': intent_data,
    })


def log_interaction(
    room_id: str,
    agent_id: str,
    event_type: str,
    target_agent_id: Optional[str] = None,
    payload: Optional[dict] = None,
    x: Optional[int] = None,
    y: Optional[int] = None
):
    """
    記錄交互日誌
    Log interaction to database

    Args:
        room_id: Room ID
        agent_id: Agent ID
        event_type: Event type
        target_agent_id: Target agent ID (optional)
        payload: Additional data (optional)
        x: X coordinate (optional)
        y: Y coordinate (optional)
    """
    from apps.agents.models import InteractionLog

    try:
        InteractionLog.objects.create(
            room_id=room_id,
            agent_id=agent_id,
            target_agent_id=target_agent_id,
            event_type=event_type,
            payload=payload or {},
            location_x=x,
            location_y=y
        )
    except Exception as e:
        logger.error(f"Failed to log interaction: {e}")


def get_recent_events(room_id: str, limit: int = 10) -> List[dict]:
    """
    獲取房間最近的事件
    Get recent events in a room

    Args:
        room_id: Room ID
        limit: Maximum number of events

    Returns:
        List of event dicts
    """
    from apps.agents.models import InteractionLog

    logs = InteractionLog.objects.filter(
        room_id=room_id
    ).select_related('agent', 'target_agent').order_by('-created_at')[:limit]

    return [
        {
            'id': str(log.id),
            'agent_id': str(log.agent_id),
            'agent_name': log.agent.name if log.agent else None,
            'target_agent_id': str(log.target_agent_id) if log.target_agent_id else None,
            'target_agent_name': log.target_agent.name if log.target_agent else None,
            'event_type': log.event_type,
            'payload': log.payload,
            'x': log.location_x,
            'y': log.location_y,
            'created_at': log.created_at.isoformat(),
        }
        for log in logs
    ]
