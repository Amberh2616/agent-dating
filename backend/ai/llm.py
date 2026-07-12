"""
LLM Service - Groq API 封裝（免費快速）
"""

import os
from typing import Optional, List, Dict, Any
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from django.conf import settings


class LLMService:
    """
    LLM 服務封裝
    Unified interface for LLM operations (using Groq)
    """

    _instance = None
    _chat_model = None
    _embedding_model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._chat_model is None:
            self._initialize_models()

    def _initialize_models(self):
        """初始化模型"""
        groq_key = getattr(settings, 'GROQ_API_KEY', None) or os.getenv('GROQ_API_KEY')

        # Chat Model (Groq - 免費快速)
        self._chat_model = ChatGroq(
            model=getattr(settings, 'GROQ_MODEL', 'llama-3.3-70b-versatile'),
            temperature=0.9,
            api_key=groq_key,
            max_tokens=1000,
        )

        # Embedding Model (暫時用 None，Groq 不支援 embedding)
        self._embedding_model = None

    @property
    def chat_model(self) -> ChatGroq:
        return self._chat_model

    @property
    def embedding_model(self):
        return self._embedding_model

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.9,
        max_tokens: int = 1000,
    ) -> str:
        """
        生成聊天回覆

        Args:
            messages: [{"role": "system|user|assistant", "content": "..."}]
            temperature: 創造性程度 (0-1)
            max_tokens: 最大 token 數

        Returns:
            生成的回覆文字
        """
        langchain_messages = []
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')

            if role == 'system':
                langchain_messages.append(SystemMessage(content=content))
            elif role == 'user':
                langchain_messages.append(HumanMessage(content=content))
            elif role == 'assistant':
                langchain_messages.append(AIMessage(content=content))

        # 臨時調整 temperature
        model = self._chat_model.with_config(
            configurable={
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
        )

        response = await model.ainvoke(langchain_messages)
        return response.content

    async def generate_embedding(self, text: str) -> List[float]:
        """
        生成文字嵌入向量

        Args:
            text: 輸入文字

        Returns:
            1536 維向量
        """
        embeddings = await self._embedding_model.aembed_documents([text])
        return embeddings[0]

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        批量生成嵌入向量

        Args:
            texts: 文字列表

        Returns:
            向量列表
        """
        return await self._embedding_model.aembed_documents(texts)

    async def analyze_soul(self, questionnaire_answers: List[Dict]) -> Dict:
        """
        分析問卷答案生成靈魂檔案

        Args:
            questionnaire_answers: 問卷答案列表

        Returns:
            靈魂檔案字典
        """
        from .prompts.soul_analysis import SOUL_ANALYSIS_PROMPT

        answers_text = "\n".join([
            f"Q{a['question_id']}: {a['question_text']}\nA: {a['answer']}"
            for a in questionnaire_answers
        ])

        messages = [
            {"role": "system", "content": SOUL_ANALYSIS_PROMPT},
            {"role": "user", "content": f"以下是用戶的問卷回答，請分析並生成靈魂檔案：\n\n{answers_text}"}
        ]

        response = await self.generate_response(messages, temperature=0.7)

        # 解析 JSON 回應
        import json
        try:
            # 嘗試提取 JSON
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass

        # 如果無法解析，返回預設結構
        return self._get_default_soul_profile()

    def _get_default_soul_profile(self) -> Dict:
        """返回預設靈魂檔案結構"""
        return {
            "worldview": {
                "optimism": 50,
                "spirituality": 50,
                "individualism": 50,
                "changeOriented": 50
            },
            "lifeview": {
                "purpose": [],
                "priorities": [],
                "lifeStage": "探索期"
            },
            "values": {
                "core": [],
                "dealbreakers": [],
                "importanceRank": {
                    "love": 3,
                    "friendship": 3,
                    "career": 3,
                    "freedom": 3,
                    "security": 3
                }
            },
            "interests": {
                "categories": [],
                "specific": {
                    "music": [],
                    "movies": [],
                    "books": [],
                    "hobbies": []
                },
                "depth": "casual"
            },
            "personality": {
                "mbti": "XXXX",
                "traits": {
                    "introversion": 50,
                    "intuition": 50,
                    "thinking": 50,
                    "judging": 50
                },
                "socialStyle": "傾聽者"
            },
            "communication_style": {
                "humor": 50,
                "depth": 50,
                "emotionality": 50,
                "preferredTopics": []
            },
            "emotional_needs": {
                "companionship": 50,
                "validation": 50,
                "stimulation": 50,
                "understanding": 50
            },
            "love_style": {
                "attachmentType": "secure",
                "loveLanguage": [],
                "romanticLevel": 50,
                "jealousy": 30
            }
        }


# 單例實例
llm_service = LLMService()
