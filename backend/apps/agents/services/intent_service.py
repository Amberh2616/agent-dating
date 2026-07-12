"""
Intent Service - 意圖/目標管理
Intent and Goal Management for Generative Agents

Handles:
- Daily goal generation
- Intent creation and decomposition
- Intent progression and completion
- Goal prioritization
"""

import json
import logging
import random
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from django.utils import timezone
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)


# Goal type to steps mapping
GOAL_STEPS = {
    'make_friend': [
        'find_target',      # 找到目標對象
        'approach',         # 靠近目標
        'greet',            # 打招呼
        'exchange_intro',   # 交換興趣
        'set_followup',     # 設定後續
    ],
    'chat_topic': [
        'find_interested',  # 找到感興趣的對象
        'approach',         # 靠近
        'start_topic',      # 開啟話題
        'discuss',          # 討論
    ],
    'explore_room': [
        'look_around',      # 環顧四周
        'move_random',      # 隨機移動
        'observe_agents',   # 觀察其他 Agent
    ],
    'follow_up': [
        'find_friend',      # 找到舊友
        'approach',         # 靠近
        'greet_friend',     # 問候
        'catch_up',         # 敘舊
    ],
    'rest': [
        'find_seat',        # 找座位
        'sit',              # 坐下
        'observe',          # 觀察
    ],
    'observe': [
        'find_spot',        # 找位置
        'watch',            # 觀看
    ],
    'socialize': [
        'scan_room',        # 掃描房間
        'choose_group',     # 選擇群組
        'join_chat',        # 加入聊天
    ],
}


# Daily goal generation prompt
DAILY_GOAL_PROMPT = """你是一個AI助手，為角色生成每日社交目標。

角色名稱: {agent_name}
角色性格: {personality}
角色興趣: {interests}
最近的反思:
{recent_reflections}

今天是 {day_of_week}，時間是 {time_of_day}。

請為這個角色生成 2-3 個適合今天的社交目標。目標應該：
1. 符合角色的性格和興趣
2. 適合當前時間段
3. 具體且可執行

目標類型可選: make_friend（認識新朋友）, chat_topic（聊特定話題）, explore_room（探索）, follow_up（跟進舊友）, rest（休息）, observe（觀察）, socialize（社交）

請用 JSON 格式回答:
{{
    "goals": [
        {{
            "goal": "目標描述",
            "goal_type": "類型",
            "priority": 1-10,
            "target_topic": "話題（可選）",
            "duration_minutes": 30-120
        }}
    ]
}}
"""


class IntentService:
    """
    意圖服務
    Intent Service for goal management

    Key functions:
    - generate_daily_goals: Create daily goals based on personality
    - create_intent: Create and decompose a goal into steps
    - advance_intent: Move to next step
    - check_completion: Check if intent is completed
    - get_active_intent: Get current active intent
    """

    def __init__(self):
        self._llm_service = None

    @property
    def llm_service(self):
        """Lazy load LLM service"""
        if self._llm_service is None:
            from ai.llm import LLMService
            self._llm_service = LLMService()
        return self._llm_service

    def generate_daily_goals(
        self,
        agent_id: str,
        language: str = 'zh-hant'
    ) -> List['AgentIntent']:
        """
        生成每日目標
        Generate daily goals for an agent

        Args:
            agent_id: Agent UUID
            language: Language preference

        Returns:
            List of created AgentIntent instances
        """
        from ..models import Agent, AgentIntent, AgentReflection

        try:
            agent = Agent.objects.select_related('user').get(id=agent_id)
        except Agent.DoesNotExist:
            logger.error(f"Agent {agent_id} not found")
            return []

        # Get personality and interests
        try:
            soul_profile = agent.user.soul_profile
            personality = soul_profile.personality or {}
            interests = soul_profile.interests or []
            personality_str = ', '.join(
                f"{k}: {v}" for k, v in personality.items()
            ) if isinstance(personality, dict) else str(personality)
            interests_str = ', '.join(interests) if isinstance(interests, list) else str(interests)
        except Exception:
            personality_str = "friendly, curious"
            interests_str = "music, travel, technology"

        # Get recent reflections
        reflections = AgentReflection.objects.filter(
            agent_id=agent_id
        ).order_by('-created_at')[:3]
        reflections_text = "\n".join([
            f"- {r.insight}" for r in reflections
        ]) or "（尚無反思）"

        # Time info
        now = timezone.now()
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_of_week = day_names[now.weekday()]
        hour = now.hour
        if 6 <= hour < 12:
            time_of_day = 'morning'
        elif 12 <= hour < 18:
            time_of_day = 'afternoon'
        elif 18 <= hour < 22:
            time_of_day = 'evening'
        else:
            time_of_day = 'night'

        prompt = DAILY_GOAL_PROMPT.format(
            agent_name=agent.name,
            personality=personality_str,
            interests=interests_str,
            recent_reflections=reflections_text,
            day_of_week=day_of_week,
            time_of_day=time_of_day
        )

        try:
            async def generate():
                messages = [
                    {"role": "system", "content": "You are an assistant that generates social goals in JSON format."},
                    {"role": "user", "content": prompt}
                ]
                return await self.llm_service.generate_response(
                    messages=messages,
                    max_tokens=500,
                    temperature=0.8
                )

            response_text = async_to_sync(generate)()

            # Parse JSON
            json_text = response_text
            if '```json' in json_text:
                json_text = json_text.split('```json')[1].split('```')[0]
            elif '```' in json_text:
                json_text = json_text.split('```')[1].split('```')[0]

            result = json.loads(json_text.strip())
            goals_data = result.get('goals', [])

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse goals JSON: {e}")
            # Fallback to default goals
            goals_data = [
                {'goal': '認識一個新朋友', 'goal_type': 'make_friend', 'priority': 7, 'duration_minutes': 60},
                {'goal': '四處逛逛', 'goal_type': 'explore_room', 'priority': 4, 'duration_minutes': 30},
            ]
        except Exception as e:
            logger.error(f"Error generating daily goals: {e}")
            goals_data = [
                {'goal': '認識一個新朋友', 'goal_type': 'make_friend', 'priority': 7, 'duration_minutes': 60},
            ]

        # Expire old pending intents
        AgentIntent.objects.filter(
            agent=agent,
            status='pending'
        ).update(status='expired')

        # Create new intents
        created_intents = []
        for g in goals_data[:3]:  # Limit to 3 goals
            goal_type = g.get('goal_type', 'socialize')
            if goal_type not in GOAL_STEPS:
                goal_type = 'socialize'

            duration = g.get('duration_minutes', 60)
            expires_at = now + timedelta(minutes=duration)

            intent = AgentIntent.objects.create(
                agent=agent,
                goal=g.get('goal', 'Socialize')[:200],
                goal_type=goal_type,
                target_topic=g.get('target_topic', '')[:100],
                status='pending',
                priority=min(10, max(1, g.get('priority', 5))),
                steps=GOAL_STEPS.get(goal_type, ['observe']),
                expires_at=expires_at
            )
            created_intents.append(intent)

        logger.info(f"Generated {len(created_intents)} daily goals for {agent.name}")
        return created_intents

    def create_intent(
        self,
        agent_id: str,
        goal: str,
        goal_type: str,
        target_agent_id: Optional[str] = None,
        target_topic: str = '',
        priority: int = 5,
        expires_minutes: int = 30
    ) -> Optional['AgentIntent']:
        """
        創建意圖並拆解步驟
        Create intent with decomposed steps

        Args:
            agent_id: Agent UUID
            goal: Goal description
            goal_type: Type of goal (make_friend, chat_topic, etc.)
            target_agent_id: Target agent UUID (optional)
            target_topic: Topic for chat_topic type
            priority: Priority 1-10
            expires_minutes: Minutes until expiration

        Returns:
            Created AgentIntent or None
        """
        from ..models import Agent, AgentIntent

        try:
            agent = Agent.objects.get(id=agent_id)
        except Agent.DoesNotExist:
            logger.error(f"Agent {agent_id} not found")
            return None

        # Get target agent if specified
        target_agent = None
        if target_agent_id:
            try:
                target_agent = Agent.objects.get(id=target_agent_id)
            except Agent.DoesNotExist:
                pass

        # Get steps for goal type
        steps = GOAL_STEPS.get(goal_type, ['observe', 'decide'])

        # Create intent
        intent = AgentIntent.objects.create(
            agent=agent,
            goal=goal[:200],
            goal_type=goal_type,
            target_agent=target_agent,
            target_topic=target_topic[:100],
            status='pending',
            priority=min(10, max(1, priority)),
            steps=steps,
            current_step=0,
            expires_at=timezone.now() + timedelta(minutes=expires_minutes)
        )

        logger.info(f"Created intent for {agent.name}: {goal}")
        return intent

    def get_active_intent(self, agent_id: str) -> Optional['AgentIntent']:
        """
        獲取當前活動的意圖
        Get current active intent for an agent

        Args:
            agent_id: Agent UUID

        Returns:
            Active AgentIntent or None
        """
        from ..models import AgentIntent

        # First check for 'active' status
        active = AgentIntent.objects.filter(
            agent_id=agent_id,
            status='active'
        ).order_by('-priority').first()

        if active:
            # Check if expired
            if active.is_expired:
                active.status = 'expired'
                active.save(update_fields=['status'])
                return None
            return active

        # If no active, get highest priority pending
        pending = AgentIntent.objects.filter(
            agent_id=agent_id,
            status='pending',
            expires_at__gt=timezone.now()
        ).order_by('-priority').first()

        return pending

    def activate_intent(self, intent_id: str) -> bool:
        """
        激活意圖
        Activate a pending intent

        Args:
            intent_id: Intent UUID

        Returns:
            True if successfully activated
        """
        from ..models import AgentIntent

        try:
            intent = AgentIntent.objects.get(id=intent_id)
            if intent.status == 'pending' and not intent.is_expired:
                intent.status = 'active'
                intent.started_at = timezone.now()
                intent.save(update_fields=['status', 'started_at'])
                return True
        except AgentIntent.DoesNotExist:
            pass

        return False

    def advance_intent(self, intent_id: str, note: str = '') -> Dict:
        """
        推進意圖到下一步
        Advance intent to next step

        Args:
            intent_id: Intent UUID
            note: Progress note to record

        Returns:
            Dict with status and next_step info
        """
        from ..models import AgentIntent

        try:
            intent = AgentIntent.objects.get(id=intent_id)
        except AgentIntent.DoesNotExist:
            return {'success': False, 'error': 'Intent not found'}

        if intent.status not in ['pending', 'active']:
            return {'success': False, 'error': f'Intent status is {intent.status}'}

        # Activate if pending
        if intent.status == 'pending':
            intent.status = 'active'
            intent.started_at = timezone.now()

        # Add progress note
        if note:
            notes = intent.progress_notes or []
            notes.append({
                'step': intent.current_step,
                'note': note,
                'time': timezone.now().isoformat()
            })
            intent.progress_notes = notes

        # Advance step
        intent.current_step += 1

        # Check completion
        if intent.current_step >= len(intent.steps):
            intent.status = 'completed'
            intent.completed_at = timezone.now()
            intent.save()
            return {
                'success': True,
                'completed': True,
                'goal': intent.goal
            }

        intent.save()
        return {
            'success': True,
            'completed': False,
            'current_step': intent.current_step,
            'step_name': intent.current_step_name,
            'remaining_steps': len(intent.steps) - intent.current_step
        }

    def check_completion(
        self,
        intent_id: str,
        context: Dict[str, Any]
    ) -> Dict:
        """
        檢查意圖是否完成
        Check if intent is completed based on context

        Args:
            intent_id: Intent UUID
            context: Current perception context

        Returns:
            Dict with is_completed and reason
        """
        from ..models import AgentIntent

        try:
            intent = AgentIntent.objects.get(id=intent_id)
        except AgentIntent.DoesNotExist:
            return {'is_completed': False, 'error': 'Intent not found'}

        # Check expiration
        if intent.is_expired:
            return {
                'is_completed': False,
                'expired': True,
                'reason': 'Intent has expired'
            }

        # Check if already completed
        if intent.status == 'completed':
            return {
                'is_completed': True,
                'reason': 'Already marked completed'
            }

        # Check step completion based on goal type
        current_step = intent.current_step_name

        if intent.goal_type == 'make_friend':
            # Check if target is now a friend
            if current_step == 'set_followup' and context.get('new_friend_made'):
                return {'is_completed': True, 'reason': 'New friend made'}

        elif intent.goal_type == 'chat_topic':
            # Check if topic was discussed
            if current_step == 'discuss' and context.get('topic_discussed'):
                return {'is_completed': True, 'reason': 'Topic discussed'}

        elif intent.goal_type in ['rest', 'observe']:
            # These are time-based
            if intent.started_at:
                elapsed = (timezone.now() - intent.started_at).total_seconds()
                if elapsed > 300:  # 5 minutes
                    return {'is_completed': True, 'reason': 'Time elapsed'}

        return {
            'is_completed': False,
            'current_step': current_step,
            'steps_remaining': len(intent.steps) - intent.current_step
        }

    def cancel_intent(self, intent_id: str, reason: str = '') -> bool:
        """
        取消意圖
        Cancel an intent

        Args:
            intent_id: Intent UUID
            reason: Cancellation reason

        Returns:
            True if successfully cancelled
        """
        from ..models import AgentIntent

        try:
            intent = AgentIntent.objects.get(id=intent_id)
            if intent.status in ['pending', 'active']:
                intent.status = 'cancelled'
                if reason:
                    notes = intent.progress_notes or []
                    notes.append({
                        'note': f'Cancelled: {reason}',
                        'time': timezone.now().isoformat()
                    })
                    intent.progress_notes = notes
                intent.save()
                return True
        except AgentIntent.DoesNotExist:
            pass

        return False

    def get_intents(
        self,
        agent_id: str,
        status: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        獲取意圖列表
        Get intents for an agent

        Args:
            agent_id: Agent UUID
            status: Filter by status (optional)
            limit: Maximum number to return

        Returns:
            List of intent dicts
        """
        from ..models import AgentIntent

        queryset = AgentIntent.objects.filter(agent_id=agent_id)
        if status:
            queryset = queryset.filter(status=status)

        intents = queryset.order_by('-priority', '-created_at')[:limit]

        return [
            {
                'id': str(i.id),
                'goal': i.goal,
                'goal_type': i.goal_type,
                'status': i.status,
                'priority': i.priority,
                'steps': i.steps,
                'current_step': i.current_step,
                'current_step_name': i.current_step_name,
                'total_steps': len(i.steps),
                'target_agent_id': str(i.target_agent_id) if i.target_agent_id else None,
                'target_topic': i.target_topic,
                'expires_at': i.expires_at.isoformat(),
                'created_at': i.created_at.isoformat(),
            }
            for i in intents
        ]

    def cleanup_expired_intents(self, agent_id: Optional[str] = None) -> int:
        """
        清理過期的意圖
        Clean up expired intents

        Args:
            agent_id: Agent UUID (optional, if None, clean all)

        Returns:
            Number of intents marked as expired
        """
        from ..models import AgentIntent

        queryset = AgentIntent.objects.filter(
            status__in=['pending', 'active'],
            expires_at__lt=timezone.now()
        )
        if agent_id:
            queryset = queryset.filter(agent_id=agent_id)

        updated = queryset.update(status='expired')
        logger.info(f"Marked {updated} intents as expired")
        return updated

    def get_suggested_action(
        self,
        intent: 'AgentIntent',
        perception: Dict[str, Any]
    ) -> Dict:
        """
        根據意圖和感知建議下一步行動
        Suggest next action based on intent and perception

        Args:
            intent: AgentIntent instance
            perception: Current perception context

        Returns:
            Action dict with type and parameters
        """
        step = intent.current_step_name
        nearby = perception.get('nearby_agents', [])

        # Map step to action
        if step == 'find_target' or step == 'find_interested' or step == 'find_friend':
            # Look for a suitable target
            if nearby:
                # Prefer targets not recently interacted with
                target = nearby[0]
                return {
                    'type': 'approach',
                    'target': target.get('id'),
                    'target_name': target.get('name'),
                }
            else:
                return {'type': 'wander', 'parameters': {}}

        elif step == 'approach':
            if intent.target_agent_id:
                return {
                    'type': 'move_to_agent',
                    'target': str(intent.target_agent_id),
                }
            elif nearby:
                return {
                    'type': 'move_to_agent',
                    'target': nearby[0].get('id'),
                }
            return {'type': 'wander', 'parameters': {}}

        elif step in ['greet', 'greet_friend']:
            return {
                'type': 'wave',
                'target': str(intent.target_agent_id) if intent.target_agent_id else None,
            }

        elif step in ['exchange_intro', 'start_topic', 'discuss', 'catch_up']:
            return {
                'type': 'chat',
                'target': str(intent.target_agent_id) if intent.target_agent_id else None,
                'topic': intent.target_topic or None,
            }

        elif step == 'look_around' or step == 'scan_room':
            return {'type': 'observe', 'parameters': {}}

        elif step == 'move_random':
            return {'type': 'wander', 'parameters': {}}

        elif step in ['observe', 'watch', 'observe_agents']:
            return {'type': 'observe', 'parameters': {}}

        elif step == 'find_seat':
            return {'type': 'find_furniture', 'furniture_type': 'seat'}

        elif step == 'sit':
            return {'type': 'sit', 'parameters': {}}

        elif step == 'set_followup':
            # Intent completion step
            return {'type': 'idle', 'note': 'Goal completed'}

        else:
            return {'type': 'idle', 'parameters': {}}


# Singleton instance
intent_service = IntentService()
