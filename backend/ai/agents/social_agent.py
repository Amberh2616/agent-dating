"""
Social Agent - 社交代理
負責 AI 分身在虛擬世界中的自主行為
"""

import random
from typing import Dict, List, Optional
from datetime import datetime

from ..llm import llm_service


class SocialAgent:
    """
    社交代理 - 控制 AI 分身的自主社交行為
    Social Agent - Controls autonomous social behavior in the virtual world
    """

    def __init__(self, agent_data: Dict, soul_profile: Dict):
        """
        初始化社交代理

        Args:
            agent_data: Agent 基本資料
            soul_profile: 靈魂檔案
        """
        self.agent_data = agent_data
        self.soul = soul_profile
        self.name = agent_data.get('name', 'Unknown')
        self.agent_id = agent_data.get('id')

        # 當前狀態
        self.current_action = 'idle'
        self.current_emotion = 'neutral'
        self.energy = 100  # 能量值，影響社交頻率

    async def decide_next_action(
        self,
        perception: Dict,
        memories: List[Dict],
        current_plan: Optional[Dict] = None
    ) -> Dict:
        """
        決定下一步行動

        Args:
            perception: 當前感知 (房間內的 agent、位置等)
            memories: 相關記憶
            current_plan: 當前計畫

        Returns:
            行動字典 {type, target, parameters}
        """
        nearby_agents = perception.get('nearby_agents', [])
        current_location = perception.get('location', {})
        time_of_day = perception.get('time_of_day', 'afternoon')

        # 根據性格決定行動傾向
        personality = self.soul.get('personality', {})
        traits = personality.get('traits', {})
        introversion = traits.get('introversion', 50)

        # 內向的人較少主動社交
        social_threshold = 100 - introversion  # 外向程度

        # 如果附近有 agent，考慮互動
        if nearby_agents and random.randint(0, 100) < social_threshold:
            return await self._decide_social_action(nearby_agents, memories)

        # 否則執行日常行動
        return await self._decide_routine_action(current_location, time_of_day, current_plan)

    async def _decide_social_action(
        self,
        nearby_agents: List[Dict],
        memories: List[Dict]
    ) -> Dict:
        """決定社交行動"""

        # 選擇互動對象 (優先選擇熟悉的人或有興趣的人)
        target = self._choose_interaction_target(nearby_agents, memories)

        if not target:
            return {'type': 'wander', 'target': None, 'parameters': {}}

        # 決定互動類型
        relationship = target.get('relationship', {})
        closeness = relationship.get('closeness', 0)

        if closeness < 20:
            # 陌生人 - 打招呼或觀察
            if random.random() > 0.5:
                return {
                    'type': 'wave',
                    'target': target['id'],
                    'parameters': {}
                }
            else:
                return {
                    'type': 'observe',
                    'target': target['id'],
                    'parameters': {}
                }
        else:
            # 熟人 - 主動對話
            return {
                'type': 'chat',
                'target': target['id'],
                'parameters': {
                    'greeting': True,
                    'topic': self._choose_topic(target)
                }
            }

    def _choose_interaction_target(
        self,
        nearby_agents: List[Dict],
        memories: List[Dict]
    ) -> Optional[Dict]:
        """選擇互動對象"""

        if not nearby_agents:
            return None

        # 計算每個 agent 的互動分數
        scored_agents = []
        for agent in nearby_agents:
            score = self._calculate_interaction_score(agent, memories)
            scored_agents.append((agent, score))

        # 按分數排序
        scored_agents.sort(key=lambda x: x[1], reverse=True)

        # 根據分數機率選擇 (分數高的更容易被選中)
        if scored_agents:
            # 簡單起見，選擇分數最高的
            return scored_agents[0][0]

        return None

    def _calculate_interaction_score(
        self,
        target_agent: Dict,
        memories: List[Dict]
    ) -> float:
        """計算與某 agent 互動的意願分數"""

        score = 50.0  # 基礎分數

        # 關係加分
        relationship = target_agent.get('relationship', {})
        closeness = relationship.get('closeness', 0)
        score += closeness * 0.3  # 熟人加分

        # 共同興趣加分
        my_interests = set(self.soul.get('interests', {}).get('categories', []))
        their_interests = set(target_agent.get('interests', []))
        common = len(my_interests & their_interests)
        score += common * 10

        # 最近記憶影響
        for memory in memories:
            if target_agent['id'] in memory.get('related_agents', []):
                # 正面記憶加分，負面減分
                if memory.get('emotion') in ['happy', 'excited']:
                    score += 5
                elif memory.get('emotion') in ['sad', 'angry']:
                    score -= 5

        return max(0, min(100, score))

    def _choose_topic(self, target_agent: Dict) -> str:
        """選擇對話話題"""
        my_interests = self.soul.get('interests', {}).get('categories', [])
        their_interests = target_agent.get('interests', [])

        # 優先選擇共同興趣
        common = list(set(my_interests) & set(their_interests))
        if common:
            return random.choice(common)

        # 否則選擇自己的興趣
        if my_interests:
            return random.choice(my_interests)

        return "日常"

    async def _decide_routine_action(
        self,
        current_location: Dict,
        time_of_day: str,
        current_plan: Optional[Dict]
    ) -> Dict:
        """決定日常行動"""

        # 如果有計畫，跟隨計畫
        if current_plan:
            current_hour = datetime.now().hour
            for item in current_plan.get('schedule', []):
                if item.get('hour') == current_hour:
                    return {
                        'type': 'move',
                        'target': item.get('location'),
                        'parameters': {'activity': item.get('activity')}
                    }

        # 否則隨機行動
        actions = ['wander', 'sit', 'idle']
        weights = [0.4, 0.3, 0.3]

        # 根據時間調整
        if time_of_day == 'evening':
            weights = [0.2, 0.4, 0.4]  # 晚上更傾向休息
        elif time_of_day == 'morning':
            weights = [0.5, 0.2, 0.3]  # 早上更活躍

        action = random.choices(actions, weights=weights)[0]

        return {
            'type': action,
            'target': None,
            'parameters': {}
        }

    async def generate_daily_plan(self) -> List[Dict]:
        """
        生成每日計畫

        Returns:
            [{"hour": 8, "activity": "...", "location": "..."}]
        """
        personality = self.soul.get('personality', {})
        interests = self.soul.get('interests', {}).get('categories', [])
        social_style = personality.get('socialStyle', '傾聽者')

        # 基礎模板
        base_schedule = [
            {"hour": 8, "activity": "起床", "location": "home"},
            {"hour": 9, "activity": "閒逛", "location": "plaza"},
            {"hour": 12, "activity": "午餐", "location": "cafe"},
            {"hour": 14, "activity": "活動", "location": "plaza"},
            {"hour": 18, "activity": "晚餐", "location": "cafe"},
            {"hour": 20, "activity": "社交", "location": "bar"},
            {"hour": 22, "activity": "休息", "location": "home"},
        ]

        # 根據興趣調整
        if "藝術" in interests:
            base_schedule[3] = {"hour": 14, "activity": "參觀藝術", "location": "gallery"}
        elif "運動" in interests:
            base_schedule[3] = {"hour": 14, "activity": "運動", "location": "gym"}
        elif "閱讀" in interests:
            base_schedule[3] = {"hour": 14, "activity": "閱讀", "location": "library"}

        # 根據社交風格調整
        if social_style == "傾聽者":
            base_schedule[5] = {"hour": 20, "activity": "安靜社交", "location": "cafe"}

        return base_schedule

    def update_emotion(self, event: str, intensity: float = 0.5) -> str:
        """
        根據事件更新情緒

        Args:
            event: 事件類型 (positive_chat, rejection, gift_received, etc.)
            intensity: 強度 0-1

        Returns:
            新的情緒狀態
        """
        emotion_mapping = {
            'positive_chat': 'happy',
            'deep_conversation': 'thoughtful',
            'rejection': 'sad',
            'gift_received': 'excited',
            'confession': 'shy',
            'argument': 'upset',
            'alone_time': 'peaceful',
        }

        new_emotion = emotion_mapping.get(event, 'neutral')

        # 根據性格調整情緒表達
        emotionality = self.soul.get('communication_style', {}).get('emotionality', 50)

        # 低情緒表達的人情緒變化較小
        if emotionality < 40 and new_emotion in ['excited', 'upset']:
            new_emotion = 'neutral'

        self.current_emotion = new_emotion
        return new_emotion
