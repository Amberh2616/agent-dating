"""
Reflection Service - 反思/洞察生成
Reflection and Insight Generation for Generative Agents

Based on Stanford Generative Agents:
- Periodically generate reflections from recent memories
- Extract higher-level understanding and insights
- Summarize conversations for context compression
"""

import json
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from django.utils import timezone
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)


# Reflection generation prompt
REFLECTION_PROMPT_ZH = """你是一個AI助手，負責分析角色的記憶並生成反思。

角色名稱: {agent_name}
角色性格: {personality}

最近的記憶:
{memories_text}

請根據這些記憶，生成 2-3 條反思/洞察。每條反思應該：
1. 總結觀察到的模式或趨勢
2. 提取關於其他人的理解
3. 識別可能的機會或興趣點

請用 JSON 格式回答:
{{
    "reflections": [
        {{
            "summary": "簡短摘要（1句話）",
            "insight": "更深層的洞察或推測",
            "importance": 5-9 的數字
        }}
    ]
}}
"""

REFLECTION_PROMPT_EN = """You are an AI assistant that analyzes a character's memories and generates reflections.

Character name: {agent_name}
Personality: {personality}

Recent memories:
{memories_text}

Based on these memories, generate 2-3 reflections/insights. Each reflection should:
1. Summarize observed patterns or trends
2. Extract understanding about other people
3. Identify potential opportunities or points of interest

Please respond in JSON format:
{{
    "reflections": [
        {{
            "summary": "Brief summary (1 sentence)",
            "insight": "Deeper insight or inference",
            "importance": number from 5-9
        }}
    ]
}}
"""


class ReflectionService:
    """
    反思服務
    Reflection Service for generating higher-level understanding

    Key functions:
    - generate_reflection: Create reflections from recent memories
    - summarize_conversation: Compress conversation into summary
    - get_reflections: Retrieve existing reflections
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

    def generate_reflection(
        self,
        agent_id: str,
        memory_count: int = 20,
        min_importance: int = 4,
        language: str = 'zh-hant'
    ) -> List['AgentReflection']:
        """
        從近期記憶生成反思
        Generate reflections from recent memories

        Args:
            agent_id: Agent UUID
            memory_count: Number of recent memories to analyze
            min_importance: Minimum memory importance to include
            language: Language for generation (zh-hant, en)

        Returns:
            List of created AgentReflection instances
        """
        from ..models import Agent, Memory, AgentReflection

        try:
            agent = Agent.objects.select_related('user').get(id=agent_id)
        except Agent.DoesNotExist:
            logger.error(f"Agent {agent_id} not found")
            return []

        # Get recent memories
        memories = Memory.objects.filter(
            agent_id=agent_id,
            importance__gte=min_importance
        ).order_by('-created_at')[:memory_count]

        if memories.count() < 3:
            logger.info(f"Not enough memories for reflection ({memories.count()} < 3)")
            return []

        # Get personality
        try:
            soul_profile = agent.user.soul_profile
            personality = soul_profile.personality or {}
            personality_str = ', '.join(
                f"{k}: {v}" for k, v in personality.items()
            ) if isinstance(personality, dict) else str(personality)
        except Exception:
            personality_str = "Unknown"

        # Format memories
        memories_text = "\n".join([
            f"- [{m.created_at.strftime('%Y-%m-%d %H:%M')}] {m.content} (重要性: {m.importance})"
            for m in memories
        ])

        # Select prompt based on language
        prompt_template = REFLECTION_PROMPT_ZH if language.startswith('zh') else REFLECTION_PROMPT_EN
        prompt = prompt_template.format(
            agent_name=agent.name,
            personality=personality_str,
            memories_text=memories_text
        )

        # Generate reflections using LLM
        try:
            async def generate():
                messages = [
                    {"role": "system", "content": "You are an AI assistant that generates reflections in JSON format."},
                    {"role": "user", "content": prompt}
                ]
                return await self.llm_service.generate_response(
                    messages=messages,
                    max_tokens=600,
                    temperature=0.7
                )

            response_text = async_to_sync(generate)()

            # Parse JSON response
            json_text = response_text
            if '```json' in json_text:
                json_text = json_text.split('```json')[1].split('```')[0]
            elif '```' in json_text:
                json_text = json_text.split('```')[1].split('```')[0]

            result = json.loads(json_text.strip())
            reflections_data = result.get('reflections', [])

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse reflection JSON: {e}")
            return []
        except Exception as e:
            logger.error(f"Error generating reflection: {e}")
            return []

        # Create reflection records
        created_reflections = []
        memory_ids = list(memories.values_list('id', flat=True))

        for r in reflections_data[:3]:  # Limit to 3 reflections
            reflection = AgentReflection.objects.create(
                agent=agent,
                summary=r.get('summary', '')[:500],
                insight=r.get('insight', '')[:500],
                importance=min(10, max(1, r.get('importance', 5)))
            )
            # Link to source memories
            reflection.based_on_memories.set(memory_ids[:10])
            created_reflections.append(reflection)

        logger.info(f"Generated {len(created_reflections)} reflections for {agent.name}")
        return created_reflections

    def summarize_conversation(
        self,
        conversation_id: str,
        language: str = 'zh-hant'
    ) -> Optional[Dict]:
        """
        對話摘要
        Summarize a conversation for memory compression

        Args:
            conversation_id: Conversation UUID
            language: Language for summary

        Returns:
            Summary dict with keys: summary, key_topics, emotional_tone
        """
        from apps.chat.models import Conversation, Message

        try:
            conversation = Conversation.objects.get(id=conversation_id)
        except Conversation.DoesNotExist:
            logger.error(f"Conversation {conversation_id} not found")
            return None

        # Get recent messages
        messages = Message.objects.filter(
            conversation_id=conversation_id
        ).order_by('-created_at')[:20]

        if messages.count() < 2:
            return None

        # Format messages
        messages_text = "\n".join([
            f"{msg.sender_type}: {msg.content}"
            for msg in reversed(messages)
        ])

        prompt = f"""請總結以下對話:

{messages_text}

用 JSON 格式回答:
{{
    "summary": "對話摘要（2-3句話）",
    "key_topics": ["話題1", "話題2"],
    "emotional_tone": "正面/中性/負面",
    "key_points": ["要點1", "要點2"]
}}
"""

        try:
            async def generate():
                messages = [
                    {"role": "system", "content": "You are an assistant that summarizes conversations in JSON format."},
                    {"role": "user", "content": prompt}
                ]
                return await self.llm_service.generate_response(
                    messages=messages,
                    max_tokens=400,
                    temperature=0.3
                )

            response_text = async_to_sync(generate)()

            # Parse JSON
            json_text = response_text
            if '```json' in json_text:
                json_text = json_text.split('```json')[1].split('```')[0]
            elif '```' in json_text:
                json_text = json_text.split('```')[1].split('```')[0]

            return json.loads(json_text.strip())

        except Exception as e:
            logger.error(f"Error summarizing conversation: {e}")
            return None

    def get_reflections(
        self,
        agent_id: str,
        limit: int = 10,
        min_importance: int = 0
    ) -> List[Dict]:
        """
        獲取反思列表
        Get reflections for an agent

        Args:
            agent_id: Agent UUID
            limit: Maximum number to return
            min_importance: Minimum importance threshold

        Returns:
            List of reflection dicts
        """
        from ..models import AgentReflection

        reflections = AgentReflection.objects.filter(
            agent_id=agent_id,
            importance__gte=min_importance
        ).order_by('-created_at')[:limit]

        return [
            {
                'id': str(r.id),
                'summary': r.summary,
                'insight': r.insight,
                'importance': r.importance,
                'created_at': r.created_at.isoformat(),
            }
            for r in reflections
        ]

    def get_recent_insights(
        self,
        agent_id: str,
        hours: int = 24,
        limit: int = 5
    ) -> List[str]:
        """
        獲取最近的洞察（純文字）
        Get recent insights as text for context injection

        Args:
            agent_id: Agent UUID
            hours: Time window in hours
            limit: Maximum number to return

        Returns:
            List of insight strings
        """
        from ..models import AgentReflection

        cutoff = timezone.now() - timedelta(hours=hours)
        reflections = AgentReflection.objects.filter(
            agent_id=agent_id,
            created_at__gte=cutoff
        ).order_by('-importance', '-created_at')[:limit]

        return [r.insight for r in reflections]

    def should_reflect(
        self,
        agent_id: str,
        memory_threshold: int = 20,
        time_threshold_hours: int = 1
    ) -> bool:
        """
        判斷是否應該進行反思
        Check if it's time for reflection

        Args:
            agent_id: Agent UUID
            memory_threshold: Min memories since last reflection
            time_threshold_hours: Min hours since last reflection

        Returns:
            True if reflection should be triggered
        """
        from ..models import Memory, AgentReflection

        # Check last reflection time
        last_reflection = AgentReflection.objects.filter(
            agent_id=agent_id
        ).order_by('-created_at').first()

        if last_reflection:
            time_since = timezone.now() - last_reflection.created_at
            if time_since < timedelta(hours=time_threshold_hours):
                return False

            # Count memories since last reflection
            new_memories = Memory.objects.filter(
                agent_id=agent_id,
                created_at__gt=last_reflection.created_at
            ).count()

            return new_memories >= memory_threshold
        else:
            # No reflections yet, check if enough memories
            memory_count = Memory.objects.filter(agent_id=agent_id).count()
            return memory_count >= memory_threshold

    def cleanup_old_reflections(
        self,
        agent_id: str,
        days: int = 30,
        keep_important: int = 7
    ) -> int:
        """
        清理舊反思（保留重要的）
        Clean up old reflections while keeping important ones

        Args:
            agent_id: Agent UUID
            days: Age threshold in days
            keep_important: Keep reflections with importance >= this

        Returns:
            Number of reflections deleted
        """
        from ..models import AgentReflection

        cutoff = timezone.now() - timedelta(days=days)
        deleted, _ = AgentReflection.objects.filter(
            agent_id=agent_id,
            created_at__lt=cutoff,
            importance__lt=keep_important
        ).delete()

        logger.info(f"Deleted {deleted} old reflections for agent {agent_id}")
        return deleted


# Singleton instance
reflection_service = ReflectionService()
