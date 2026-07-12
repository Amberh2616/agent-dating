"""
Memory Service - 記憶流管理
Memory Stream Management for Generative Agents

Handles:
- Memory creation with embeddings
- Retrieval by recency, importance, and relevance (vector similarity)
- Combined retrieval for decision making
"""

import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q, F
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)


class MemoryService:
    """
    記憶流管理服務
    Memory Stream Management Service

    Based on Stanford Generative Agents paper:
    - Recency: Recent memories are more relevant
    - Importance: Important memories should be prioritized
    - Relevance: Semantic similarity to current context
    """

    def __init__(self):
        self._llm_service = None
        self._embedding_cache = {}

    @property
    def llm_service(self):
        """Lazy load LLM service"""
        if self._llm_service is None:
            from ai.llm import LLMService
            self._llm_service = LLMService()
        return self._llm_service

    def add_memory(
        self,
        agent_id: str,
        content: str,
        memory_type: str = 'observation',
        importance: int = 5,
        related_agents: Optional[List[str]] = None,
        location: Optional[Dict] = None,
        emotion: str = '',
        generate_embedding: bool = True
    ) -> 'Memory':
        """
        寫入記憶 + 生成嵌入向量
        Add memory with optional embedding generation

        Args:
            agent_id: Agent UUID
            content: Memory content
            memory_type: observation | reflection | plan | conversation | emotion
            importance: 1-10 importance score
            related_agents: List of related agent IDs
            location: Location dict {room_id, x, y}
            emotion: Current emotion state
            generate_embedding: Whether to generate embedding vector

        Returns:
            Created Memory instance
        """
        from ..models import Agent, Memory

        try:
            agent = Agent.objects.get(id=agent_id)
        except Agent.DoesNotExist:
            logger.error(f"Agent {agent_id} not found")
            raise ValueError(f"Agent {agent_id} not found")

        # Calculate importance if not provided
        if importance == 5:
            importance = self._calculate_importance(content, memory_type)

        # Create memory
        memory = Memory.objects.create(
            agent=agent,
            type=memory_type,
            content=content,
            importance=importance,
            related_agents=related_agents or [],
            location=location or {},
            emotion=emotion
        )

        # Generate embedding asynchronously (optional for performance)
        if generate_embedding:
            try:
                embedding = self._generate_embedding(content)
                if embedding:
                    memory.embedding = embedding
                    memory.save(update_fields=['embedding'])
            except Exception as e:
                logger.warning(f"Failed to generate embedding: {e}")

        logger.debug(f"Created memory for {agent.name}: {content[:50]}...")
        return memory

    def get_recent(self, agent_id: str, limit: int = 10) -> List[Dict]:
        """
        取最近 N 條記憶
        Get most recent N memories

        Args:
            agent_id: Agent UUID
            limit: Maximum number of memories to return

        Returns:
            List of memory dicts
        """
        from ..models import Memory

        memories = Memory.objects.filter(
            agent_id=agent_id
        ).order_by('-created_at')[:limit]

        return self._format_memories(memories)

    def get_important(
        self,
        agent_id: str,
        min_importance: int = 7,
        limit: int = 5
    ) -> List[Dict]:
        """
        取重要記憶
        Get important memories (importance >= threshold)

        Args:
            agent_id: Agent UUID
            min_importance: Minimum importance score (1-10)
            limit: Maximum number to return

        Returns:
            List of memory dicts
        """
        from ..models import Memory

        memories = Memory.objects.filter(
            agent_id=agent_id,
            importance__gte=min_importance
        ).order_by('-importance', '-created_at')[:limit]

        return self._format_memories(memories)

    def get_similar(
        self,
        agent_id: str,
        query_text: str,
        limit: int = 5,
        min_similarity: float = 0.5
    ) -> List[Dict]:
        """
        取語義相似記憶（向量檢索）
        Get semantically similar memories using vector search

        Args:
            agent_id: Agent UUID
            query_text: Query text to find similar memories
            limit: Maximum number to return
            min_similarity: Minimum cosine similarity threshold

        Returns:
            List of memory dicts with similarity scores
        """
        from ..models import Memory

        # Generate query embedding
        query_embedding = self._generate_embedding(query_text)
        if not query_embedding:
            # Fallback to keyword search
            return self._keyword_search(agent_id, query_text, limit)

        # Get all memories with embeddings
        memories = Memory.objects.filter(
            agent_id=agent_id
        ).exclude(embedding=[])

        # Calculate similarities
        results = []
        for memory in memories:
            if memory.embedding:
                similarity = self._cosine_similarity(query_embedding, memory.embedding)
                if similarity >= min_similarity:
                    results.append({
                        'memory': memory,
                        'similarity': similarity
                    })

        # Sort by similarity
        results.sort(key=lambda x: x['similarity'], reverse=True)

        # Format results
        formatted = []
        for r in results[:limit]:
            m = self._format_memory(r['memory'])
            m['similarity'] = round(r['similarity'], 3)
            formatted.append(m)

        return formatted

    def get_by_agent(
        self,
        agent_id: str,
        related_agent_id: str,
        limit: int = 10
    ) -> List[Dict]:
        """
        取與特定 Agent 相關的記憶
        Get memories related to a specific agent

        Args:
            agent_id: Agent UUID
            related_agent_id: Related agent's UUID
            limit: Maximum number to return

        Returns:
            List of memory dicts
        """
        from ..models import Memory

        memories = Memory.objects.filter(
            agent_id=agent_id,
            related_agents__contains=[related_agent_id]
        ).order_by('-created_at')[:limit]

        return self._format_memories(memories)

    def retrieve_for_decision(
        self,
        agent_id: str,
        context: Dict[str, Any],
        max_memories: int = 15
    ) -> List[Dict]:
        """
        綜合檢索：最近 + 相關 + 重要
        Combined retrieval for decision making

        Uses weighted combination of:
        - Recency (40%): Most recent memories
        - Importance (30%): High-importance memories
        - Relevance (30%): Context-relevant memories

        Args:
            agent_id: Agent UUID
            context: Perception context dict with keys like:
                - nearby_agents: List of nearby agent data
                - room_type: Current room type
                - time_of_day: morning/afternoon/evening/night
            max_memories: Maximum total memories to return

        Returns:
            Deduplicated list of memory dicts with retrieval_score
        """
        from ..models import Memory

        memory_scores = {}  # memory_id -> score

        # 1. Recent memories (40% weight)
        recent_count = int(max_memories * 0.4)
        recent = Memory.objects.filter(
            agent_id=agent_id
        ).order_by('-created_at')[:recent_count]

        for i, m in enumerate(recent):
            recency_score = 1.0 - (i / max(recent_count, 1)) * 0.5
            memory_scores[str(m.id)] = {
                'memory': m,
                'recency': recency_score,
                'importance': 0,
                'relevance': 0
            }

        # 2. Important memories (30% weight)
        important_count = int(max_memories * 0.3)
        important = Memory.objects.filter(
            agent_id=agent_id,
            importance__gte=6
        ).order_by('-importance', '-created_at')[:important_count]

        for m in important:
            importance_score = m.importance / 10.0
            if str(m.id) in memory_scores:
                memory_scores[str(m.id)]['importance'] = importance_score
            else:
                memory_scores[str(m.id)] = {
                    'memory': m,
                    'recency': 0.3,  # Base recency for older important memories
                    'importance': importance_score,
                    'relevance': 0
                }

        # 3. Relevant memories (30% weight) - based on context
        # Build query from context
        context_parts = []
        if context.get('nearby_agents'):
            agent_names = [a.get('name', '') for a in context['nearby_agents'][:3]]
            context_parts.append(' '.join(agent_names))
        if context.get('room_type'):
            context_parts.append(context['room_type'])
        if context.get('time_of_day'):
            context_parts.append(context['time_of_day'])

        if context_parts:
            query = ' '.join(context_parts)
            relevant_count = int(max_memories * 0.3)

            # Try vector search first
            similar = self.get_similar(agent_id, query, limit=relevant_count)
            for m_dict in similar:
                mid = m_dict.get('id')
                relevance_score = m_dict.get('similarity', 0.5)
                if mid in memory_scores:
                    memory_scores[mid]['relevance'] = relevance_score
                else:
                    # Need to fetch the memory object
                    try:
                        memory = Memory.objects.get(id=mid)
                        memory_scores[mid] = {
                            'memory': memory,
                            'recency': 0.2,
                            'importance': memory.importance / 10.0,
                            'relevance': relevance_score
                        }
                    except Memory.DoesNotExist:
                        pass

        # Calculate final scores and sort
        results = []
        for mid, data in memory_scores.items():
            final_score = (
                data['recency'] * 0.4 +
                data['importance'] * 0.3 +
                data['relevance'] * 0.3
            )
            m_dict = self._format_memory(data['memory'])
            m_dict['retrieval_score'] = round(final_score, 3)
            m_dict['recency_score'] = round(data['recency'], 3)
            m_dict['importance_score'] = round(data['importance'], 3)
            m_dict['relevance_score'] = round(data['relevance'], 3)
            results.append(m_dict)

        # Sort by final score and limit
        results.sort(key=lambda x: x['retrieval_score'], reverse=True)
        return results[:max_memories]

    def update_access(self, memory_id: str) -> None:
        """
        更新記憶的存取時間和次數
        Update memory access time and count

        Args:
            memory_id: Memory UUID
        """
        from ..models import Memory

        Memory.objects.filter(id=memory_id).update(
            last_accessed=timezone.now(),
            access_count=F('access_count') + 1
        )

    def decay_old_memories(
        self,
        agent_id: str,
        days: int = 30,
        decay_factor: float = 0.9
    ) -> int:
        """
        衰減舊記憶的重要性
        Decay importance of old memories

        Args:
            agent_id: Agent UUID
            days: Age threshold in days
            decay_factor: Multiply importance by this factor

        Returns:
            Number of memories decayed
        """
        from ..models import Memory

        cutoff = timezone.now() - timedelta(days=days)
        updated = Memory.objects.filter(
            agent_id=agent_id,
            created_at__lt=cutoff,
            importance__gt=1
        ).update(
            importance=F('importance') * decay_factor
        )

        logger.info(f"Decayed {updated} memories for agent {agent_id}")
        return updated

    # === Private Methods ===

    def _calculate_importance(self, content: str, memory_type: str) -> int:
        """Calculate importance score based on content and type"""
        base_scores = {
            'observation': 3,
            'conversation': 5,
            'emotion': 6,
            'reflection': 7,
            'plan': 6,
        }
        base = base_scores.get(memory_type, 5)

        # Keywords that increase importance
        important_keywords = [
            '愛', '喜歡', '討厭', '重要', '驚訝', '朋友', '約會',
            'love', 'like', 'hate', 'important', 'surprise', 'friend', 'date'
        ]
        for keyword in important_keywords:
            if keyword in content.lower():
                base = min(10, base + 1)

        return base

    def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding vector for text"""
        # Check cache
        cache_key = hash(text[:100])
        if cache_key in self._embedding_cache:
            return self._embedding_cache[cache_key]

        try:
            # Use OpenAI or local embedding model
            # For now, return None to skip embedding (can be implemented later)
            # This is a placeholder for actual embedding generation
            return None
        except Exception as e:
            logger.warning(f"Embedding generation failed: {e}")
            return None

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def _keyword_search(
        self,
        agent_id: str,
        query: str,
        limit: int = 5
    ) -> List[Dict]:
        """Fallback keyword-based search"""
        from ..models import Memory

        words = query.lower().split()
        q = Q()
        for word in words:
            if len(word) > 2:
                q |= Q(content__icontains=word)

        if not q:
            return []

        memories = Memory.objects.filter(
            Q(agent_id=agent_id) & q
        ).order_by('-created_at')[:limit]

        return self._format_memories(memories)

    def _format_memory(self, memory: 'Memory') -> Dict:
        """Format a single memory object to dict"""
        return {
            'id': str(memory.id),
            'type': memory.type,
            'content': memory.content,
            'importance': memory.importance,
            'related_agents': memory.related_agents,
            'location': memory.location,
            'emotion': memory.emotion,
            'created_at': memory.created_at.isoformat(),
        }

    def _format_memories(self, memories) -> List[Dict]:
        """Format multiple memory objects to list of dicts"""
        return [self._format_memory(m) for m in memories]


# Singleton instance
memory_service = MemoryService()
