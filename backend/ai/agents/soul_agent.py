"""
Soul Agent - 靈魂代理
代表用戶靈魂的 AI Agent，負責生成符合用戶人格的回應
"""

from typing import Dict, List, Optional
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from ..llm import llm_service
from ..prompts.dialogue import DIALOGUE_SYSTEM_PROMPT, FIRST_CHAT_PROMPT
from ..prompts.speaking_styles import generate_speaking_style


class SoulAgent:
    """
    靈魂代理 - 代表用戶的 AI 分身
    Soul Agent - AI representation of a user's soul
    """

    def __init__(self, agent_data: Dict, soul_profile: Dict):
        """
        初始化靈魂代理

        Args:
            agent_data: Agent 基本資料 (name, id, etc.)
            soul_profile: 靈魂檔案 (SoulProfile model data)
        """
        self.agent_data = agent_data
        self.soul = soul_profile
        self.name = agent_data.get('name', 'Unknown')
        self.agent_id = agent_data.get('id')

        # 對話記憶 (簡化版)
        self.chat_history = []

    def _build_system_prompt(
        self,
        other_name: str,
        relationship_stage: str,
        closeness: int,
        romantic: int,
        context: str = "",
        response_language: str = "繁體中文",
        memories: str = "",
        emotion_description: str = "",
        reflections: str = ""
    ) -> str:
        """構建系統提示語"""

        # 世界觀描述
        worldview = self.soul.get('worldview', {})
        worldview_desc = self._describe_worldview(worldview)

        # 人生觀描述
        lifeview = self.soul.get('lifeview', {})
        lifeview_desc = self._describe_lifeview(lifeview)

        # 價值觀描述
        values = self.soul.get('values', {})
        values_desc = self._describe_values(values)

        # 興趣描述
        interests = self.soul.get('interests', {})
        interests_desc = self._describe_interests(interests)

        # 性格
        personality = self.soul.get('personality', {})
        mbti = personality.get('mbti', 'XXXX')
        social_style = personality.get('socialStyle', '傾聽者')
        traits = personality.get('traits', {})
        introversion = traits.get('introversion', 50)

        # 對話風格
        comm_style = self.soul.get('communication_style', {})
        humor = comm_style.get('humor', 50)
        depth = comm_style.get('depth', 50)
        emotionality = comm_style.get('emotionality', 50)
        topics = ', '.join(comm_style.get('preferredTopics', []))

        # 情感需求
        emotional = self.soul.get('emotional_needs', {})
        companionship = emotional.get('companionship', 50)
        understanding = emotional.get('understanding', 50)

        # 戀愛特質
        love_style = self.soul.get('love_style', {})
        attachment = love_style.get('attachmentType', 'secure')
        love_lang = ', '.join(love_style.get('loveLanguage', []))
        romantic_level = love_style.get('romanticLevel', 50)

        # 生成說話風格指引
        speaking_style = generate_speaking_style(
            personality=personality,
            communication_style=comm_style,
            emotional_needs=emotional
        )

        return DIALOGUE_SYSTEM_PROMPT.format(
            agent_name=self.name,
            response_language=response_language,
            worldview_description=worldview_desc,
            lifeview_description=lifeview_desc,
            values_description=values_desc,
            interests_description=interests_desc,
            mbti=mbti,
            social_style=social_style,
            introversion_level="內向" if introversion > 60 else "外向" if introversion < 40 else "中等",
            humor_level=humor,
            depth_level=depth,
            emotionality_level=emotionality,
            preferred_topics=topics,
            companionship_level=companionship,
            understanding_level=understanding,
            speaking_style=speaking_style,
            attachment_type=attachment,
            love_language=love_lang,
            romantic_level=romantic_level,
            other_name=other_name,
            relationship_stage=relationship_stage,
            closeness=closeness,
            romantic=romantic,
            context=context,
            memories=memories if memories else "（尚無與對方的互動記憶）",
            emotion_description=emotion_description if emotion_description else "情緒平穩",
            reflections=reflections if reflections else "（尚無反思）",
        )

    def _describe_worldview(self, worldview: Dict) -> str:
        """將世界觀數值轉換為描述"""
        optimism = worldview.get('optimism', 50)
        individ = worldview.get('individualism', 50)
        change = worldview.get('changeOriented', 50)

        parts = []
        if optimism > 70:
            parts.append("樂觀積極")
        elif optimism < 30:
            parts.append("偏向現實主義")

        if individ > 70:
            parts.append("重視個人獨立")
        elif individ < 30:
            parts.append("重視群體和諧")

        if change > 70:
            parts.append("喜歡嘗試新事物")
        elif change < 30:
            parts.append("偏好穩定傳統")

        return '、'.join(parts) if parts else "平衡中庸"

    def _describe_lifeview(self, lifeview: Dict) -> str:
        """將人生觀轉換為描述"""
        purpose = lifeview.get('purpose', [])
        priorities = lifeview.get('priorities', [])
        stage = lifeview.get('lifeStage', '探索期')

        desc = f"人生階段：{stage}"
        if purpose:
            desc += f"，追求{'/'.join(purpose[:2])}"
        if priorities:
            desc += f"，優先重視{'/'.join(priorities[:2])}"

        return desc

    def _describe_values(self, values: Dict) -> str:
        """將價值觀轉換為描述"""
        core = values.get('core', [])
        dealbreakers = values.get('dealbreakers', [])

        desc = ""
        if core:
            desc += f"核心價值：{', '.join(core)}"
        if dealbreakers:
            desc += f"；絕對無法接受：{', '.join(dealbreakers)}"

        return desc or "開放包容"

    def _describe_interests(self, interests: Dict) -> str:
        """將興趣轉換為描述"""
        categories = interests.get('categories', [])
        specific = interests.get('specific', {})
        depth = interests.get('depth', 'casual')

        depth_desc = {
            'casual': '輕度愛好者',
            'enthusiast': '熱愛者',
            'expert': '專家級'
        }.get(depth, '愛好者')

        desc = f"興趣領域：{', '.join(categories[:4])}" if categories else ""

        specifics = []
        for key, values in specific.items():
            if values:
                specifics.extend(values[:2])

        if specifics:
            desc += f"（具體：{', '.join(specifics[:4])}）"

        if desc:
            desc += f"，{depth_desc}"

        return desc or "興趣廣泛"

    async def generate_response(
        self,
        message: str,
        other_agent_data: Dict,
        relationship_data: Dict,
        conversation_context: Optional[List[Dict]] = None,
        response_language: str = None,
        memories: Optional[List[Dict]] = None,
        emotion_description: str = "",
        reflections: Optional[List[str]] = None
    ) -> str:
        """
        生成對話回應

        Args:
            message: 對方的訊息
            other_agent_data: 對方 Agent 資料
            relationship_data: 關係資料
            conversation_context: 對話上下文
            response_language: 回應語言（如 "Español", "English", "日本語"）
            memories: 與對方相關的記憶列表
            emotion_description: 當前情緒描述
            reflections: 最近的反思/洞察列表

        Returns:
            生成的回應文字
        """
        other_name = other_agent_data.get('name', '對方')
        relationship_stage = relationship_data.get('stage', 'stranger')
        closeness = relationship_data.get('closeness', 0)
        romantic = relationship_data.get('romantic', 0)

        # 決定回應語言：優先使用傳入的語言，否則從對方資料取得，預設繁中
        if not response_language:
            response_language = other_agent_data.get('preferred_language', '繁體中文')

        # 構建上下文
        context = ""
        if conversation_context:
            context = "最近的對話：\n"
            for msg in conversation_context[-5:]:
                role = "你" if msg.get('sender_type') == 'agent' else other_name
                context += f"{role}: {msg.get('content', '')}\n"

        # 格式化記憶
        memories_text = ""
        if memories:
            memories_text = "\n".join([
                f"- [{m.get('type', 'memory')}] {m.get('content', '')} (重要性: {m.get('importance', 5)}/10)"
                for m in memories[:10]  # 最多 10 條記憶
            ])

        # 格式化反思
        reflections_text = ""
        if reflections:
            reflections_text = "\n".join([
                f"- {r}" for r in reflections[:5]  # 最多 5 條反思
            ])

        # 構建系統提示
        system_prompt = self._build_system_prompt(
            other_name=other_name,
            relationship_stage=self._translate_stage(relationship_stage),
            closeness=closeness,
            romantic=romantic,
            context=context,
            response_language=response_language,
            memories=memories_text,
            emotion_description=emotion_description,
            reflections=reflections_text
        )

        # 準備訊息
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"{other_name}: {message}"}
        ]

        # 生成回應
        response = await llm_service.generate_response(
            messages,
            temperature=0.9,
            max_tokens=500
        )

        # 儲存到記憶
        self.chat_history.append({"input": message, "output": response})
        # 保留最近 20 輪
        if len(self.chat_history) > 20:
            self.chat_history = self.chat_history[-20:]

        return response

    async def generate_first_message(
        self,
        other_agent_data: Dict,
        other_soul_profile: Dict,
        response_language: str = None
    ) -> str:
        """
        生成第一條打招呼訊息

        Args:
            other_agent_data: 對方 Agent 資料
            other_soul_profile: 對方靈魂檔案
            response_language: 回應語言

        Returns:
            打招呼訊息
        """
        other_name = other_agent_data.get('name', '你')

        # 決定回應語言
        if not response_language:
            response_language = other_agent_data.get('preferred_language', '繁體中文')

        # 找出共同興趣
        my_interests = self.soul.get('interests', {}).get('categories', [])
        their_interests = other_soul_profile.get('interests', {}).get('categories', [])
        common_interests = list(set(my_interests) & set(their_interests))

        other_info = ""
        if common_interests:
            other_info = f"你們有共同興趣：{', '.join(common_interests[:3])}"

        system_prompt = self._build_system_prompt(
            other_name=other_name,
            relationship_stage="陌生人",
            closeness=0,
            romantic=0,
            context=FIRST_CHAT_PROMPT.format(
                agent_name=self.name,
                other_name=other_name,
                other_info=other_info
            ),
            response_language=response_language
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"請向 {other_name} 打招呼並開始對話。"}
        ]

        return await llm_service.generate_response(
            messages,
            temperature=0.9,
            max_tokens=200
        )

    def _translate_stage(self, stage: str) -> str:
        """將關係階段翻譯為中文"""
        translations = {
            'stranger': '陌生人',
            'acquaintance': '認識',
            'friend': '朋友',
            'close_friend': '好友',
            'crush': '曖昧',
            'lover': '戀人',
            'partner': '伴侶',
        }
        return translations.get(stage, stage)

    def get_personality_summary(self) -> str:
        """獲取性格摘要"""
        personality = self.soul.get('personality', {})
        mbti = personality.get('mbti', 'XXXX')
        social_style = personality.get('socialStyle', '傾聽者')

        values = self.soul.get('values', {})
        core = ', '.join(values.get('core', [])[:3])

        return f"{self.name} 是 {mbti} 類型的 {social_style}，核心價值觀是{core}。"
