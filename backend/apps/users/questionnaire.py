"""
問卷系統
Questionnaire System for Soul Profile Generation
"""

from typing import List, Dict

# 15 題問卷
QUESTIONNAIRE = [
    # === 三觀問題 (6題) ===
    {
        "id": 1,
        "category": "lifeview",
        "question": "你認為人生最重要的是什麼？",
        "type": "multiple_choice",
        "options": [
            {"value": "happiness", "label": "追求快樂和享受生活"},
            {"value": "achievement", "label": "實現自我和達成目標"},
            {"value": "helping", "label": "幫助他人和貢獻社會"},
            {"value": "experience", "label": "體驗世界和拓展視野"},
            {"value": "connection", "label": "建立深厚的人際關係"},
        ],
        "allow_multiple": True,
        "max_selections": 2,
    },
    {
        "id": 2,
        "category": "worldview",
        "question": "面對困難時，你通常會怎麼想？",
        "type": "scale",
        "scale_labels": {
            "left": "事情總會變好的",
            "right": "需要務實面對現實"
        },
        "analysis_field": "optimism",  # 數值越高越樂觀
    },
    {
        "id": 3,
        "category": "worldview",
        "question": "你更重視個人成就還是群體和諧？",
        "type": "scale",
        "scale_labels": {
            "left": "個人成就和獨立",
            "right": "群體和諧與團隊"
        },
        "analysis_field": "individualism",  # 數值越高越個人主義
    },
    {
        "id": 4,
        "category": "values",
        "question": "對你來說，什麼是絕對不能接受的？（可多選）",
        "type": "multiple_choice",
        "options": [
            {"value": "dishonesty", "label": "欺騙和不誠實"},
            {"value": "coldness", "label": "冷漠和缺乏同理心"},
            {"value": "arrogance", "label": "傲慢和瞧不起人"},
            {"value": "laziness", "label": "懶惰和不負責任"},
            {"value": "control", "label": "控制慾強和不尊重"},
            {"value": "superficial", "label": "膚淺和只看外表"},
        ],
        "allow_multiple": True,
        "max_selections": 3,
        "analysis_field": "dealbreakers",
    },
    {
        "id": 5,
        "category": "lifeview",
        "question": "你現在人生階段的首要目標是什麼？",
        "type": "single_choice",
        "options": [
            {"value": "explore", "label": "探索自我，找到方向"},
            {"value": "career", "label": "事業發展，追求成就"},
            {"value": "stability", "label": "穩定生活，平衡各方面"},
            {"value": "relationship", "label": "找到伴侶，建立家庭"},
            {"value": "enjoy", "label": "享受生活，追求體驗"},
        ],
        "analysis_field": "lifeStage",
    },
    {
        "id": 6,
        "category": "values",
        "question": "什麼事情會讓你感到生活有意義？（可多選）",
        "type": "multiple_choice",
        "options": [
            {"value": "create", "label": "創造新事物"},
            {"value": "learn", "label": "學習新知識"},
            {"value": "connect", "label": "與人深度連結"},
            {"value": "help", "label": "幫助他人"},
            {"value": "achieve", "label": "達成目標"},
            {"value": "enjoy", "label": "享受當下"},
        ],
        "allow_multiple": True,
        "max_selections": 3,
        "analysis_field": "core_values",
    },

    # === 興趣問題 (5題) ===
    {
        "id": 7,
        "category": "interests",
        "question": "週末你最想做什麼？",
        "type": "multiple_choice",
        "options": [
            {"value": "outdoors", "label": "戶外活動（運動、旅行、露營）"},
            {"value": "social", "label": "社交活動（聚會、約會、聊天）"},
            {"value": "creative", "label": "創作活動（繪畫、音樂、寫作）"},
            {"value": "learning", "label": "學習活動（閱讀、上課、研究）"},
            {"value": "relaxing", "label": "放鬆活動（追劇、遊戲、發呆）"},
            {"value": "cooking", "label": "美食活動（烹飪、探店、品嚐）"},
        ],
        "allow_multiple": True,
        "max_selections": 2,
    },
    {
        "id": 8,
        "category": "interests",
        "question": "最近讓你興奮或感興趣的話題是什麼？",
        "type": "text",
        "placeholder": "例如：AI 技術、某部電影、某個哲學問題...",
        "analysis_hint": "用於分析興趣深度和具體領域",
    },
    {
        "id": 9,
        "category": "interests",
        "question": "你偏好什麼類型的音樂/電影/書籍？",
        "type": "tags",
        "tag_categories": {
            "music": ["流行", "獨立音樂", "古典", "電子", "嘻哈", "搖滾", "爵士", "R&B"],
            "movies": ["愛情片", "科幻", "紀錄片", "文藝片", "喜劇", "動作", "恐怖", "動畫"],
            "books": ["小說", "心理學", "哲學", "商業", "科普", "傳記", "詩歌", "漫畫"],
        },
        "allow_multiple_per_category": True,
        "max_per_category": 3,
    },
    {
        "id": 10,
        "category": "interests",
        "question": "你願意花時間深入研究的領域是？",
        "type": "single_choice",
        "options": [
            {"value": "tech", "label": "科技與創新"},
            {"value": "art", "label": "藝術與設計"},
            {"value": "nature", "label": "自然與環境"},
            {"value": "psychology", "label": "心理與人性"},
            {"value": "business", "label": "商業與經濟"},
            {"value": "culture", "label": "文化與歷史"},
            {"value": "fitness", "label": "健身與運動"},
        ],
        "analysis_field": "interest_depth",
    },
    {
        "id": 11,
        "category": "interests",
        "question": "你理想的社交活動是什麼？",
        "type": "single_choice",
        "options": [
            {"value": "one_on_one", "label": "一對一深度對話"},
            {"value": "small_group", "label": "小團體聚會 (3-5人)"},
            {"value": "party", "label": "大型派對或活動"},
            {"value": "online", "label": "線上社交"},
            {"value": "activity", "label": "一起做某件事（運動、遊戲等）"},
        ],
    },

    # === 性格/情感問題 (4題) ===
    {
        "id": 12,
        "category": "personality",
        "question": "在聚會中，你通常是...？",
        "type": "scale",
        "scale_labels": {
            "left": "主動找人聊天，認識新朋友",
            "right": "等待別人來找我，或和熟人待在一起"
        },
        "analysis_field": "introversion",  # 數值越高越內向
    },
    {
        "id": 13,
        "category": "communication",
        "question": "你喜歡的聊天方式是...？",
        "type": "multiple_choice",
        "options": [
            {"value": "deep", "label": "深度話題（人生、哲學、夢想）"},
            {"value": "humor", "label": "輕鬆幽默（開玩笑、吐槽）"},
            {"value": "sharing", "label": "互相分享（日常、感受）"},
            {"value": "debate", "label": "觀點討論（時事、看法）"},
            {"value": "support", "label": "傾聽支持（陪伴、安慰）"},
        ],
        "allow_multiple": True,
        "max_selections": 2,
    },
    {
        "id": 14,
        "category": "emotional",
        "question": "什麼讓你感到被理解和被關心？",
        "type": "multiple_choice",
        "options": [
            {"value": "words", "label": "聽到肯定和鼓勵的話"},
            {"value": "time", "label": "對方花時間陪伴我"},
            {"value": "gifts", "label": "收到貼心的禮物"},
            {"value": "help", "label": "對方主動幫助我"},
            {"value": "touch", "label": "肢體上的親密接觸"},
        ],
        "allow_multiple": True,
        "max_selections": 2,
        "analysis_field": "love_language",
    },
    {
        "id": 15,
        "category": "personality",
        "question": "你需要多少獨處時間？",
        "type": "scale",
        "scale_labels": {
            "left": "不太需要，喜歡和人在一起",
            "right": "很需要，經常需要獨處充電"
        },
        "analysis_field": "alone_time_need",
    },
]


def get_questionnaire() -> List[Dict]:
    """獲取完整問卷"""
    return QUESTIONNAIRE


def get_question_by_id(question_id: int) -> Dict:
    """根據 ID 獲取單題"""
    for q in QUESTIONNAIRE:
        if q['id'] == question_id:
            return q
    return None


def validate_answer(question_id: int, answer) -> bool:
    """驗證答案格式"""
    question = get_question_by_id(question_id)
    if not question:
        return False

    q_type = question.get('type')

    if q_type == 'multiple_choice':
        if question.get('allow_multiple'):
            if not isinstance(answer, list):
                return False
            max_sel = question.get('max_selections', 3)
            if len(answer) > max_sel:
                return False
        else:
            if not isinstance(answer, str):
                return False

    elif q_type == 'single_choice':
        if not isinstance(answer, str):
            return False

    elif q_type == 'scale':
        if not isinstance(answer, (int, float)):
            return False
        if answer < 0 or answer > 100:
            return False

    elif q_type == 'text':
        if not isinstance(answer, str):
            return False

    elif q_type == 'tags':
        if not isinstance(answer, dict):
            return False

    return True


class QuestionnaireAnalyzer:
    """問卷分析器 - 將答案轉換為靈魂檔案"""

    def analyze(self, responses: List[Dict]) -> Dict:
        """
        分析問卷回答，生成初步靈魂檔案

        Args:
            responses: [{"question_id": 1, "answer": "..."}]

        Returns:
            靈魂檔案字典
        """
        profile = self._get_empty_profile()

        # 建立回答映射
        answers = {r['question_id']: r['answer'] for r in responses}

        # 分析各個問題
        self._analyze_lifeview(profile, answers)
        self._analyze_worldview(profile, answers)
        self._analyze_values(profile, answers)
        self._analyze_interests(profile, answers)
        self._analyze_personality(profile, answers)
        self._analyze_communication(profile, answers)
        self._analyze_emotional(profile, answers)

        return profile

    def _get_empty_profile(self) -> Dict:
        """獲取空白靈魂檔案結構"""
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
            },
            "relationship_behavior": {
                "initiativeLevel": 50,
                "expressiveness": 50,
                "supportStyle": "傾聽型"
            }
        }

    def _analyze_lifeview(self, profile: Dict, answers: Dict):
        """分析人生觀"""
        # Q1: 人生最重要的是什麼
        if 1 in answers:
            mapping = {
                "happiness": "追求快樂",
                "achievement": "實現自我",
                "helping": "幫助他人",
                "experience": "體驗世界",
                "connection": "建立關係"
            }
            profile['lifeview']['purpose'] = [
                mapping.get(a, a) for a in answers[1] if a in mapping
            ]

        # Q5: 人生階段
        if 5 in answers:
            stage_mapping = {
                "explore": "探索期",
                "career": "奮鬥期",
                "stability": "穩定期",
                "relationship": "奮鬥期",
                "enjoy": "享受期"
            }
            profile['lifeview']['lifeStage'] = stage_mapping.get(
                answers[5], "探索期"
            )

    def _analyze_worldview(self, profile: Dict, answers: Dict):
        """分析世界觀"""
        # Q2: 樂觀程度
        if 2 in answers:
            profile['worldview']['optimism'] = int(answers[2])

        # Q3: 個人/群體
        if 3 in answers:
            profile['worldview']['individualism'] = int(answers[3])

    def _analyze_values(self, profile: Dict, answers: Dict):
        """分析價值觀"""
        # Q4: 底線
        if 4 in answers:
            mapping = {
                "dishonesty": "欺騙",
                "coldness": "冷漠",
                "arrogance": "傲慢",
                "laziness": "懶惰",
                "control": "控制",
                "superficial": "膚淺"
            }
            profile['values']['dealbreakers'] = [
                mapping.get(a, a) for a in answers[4] if a in mapping
            ]

        # Q6: 核心價值
        if 6 in answers:
            mapping = {
                "create": "創意",
                "learn": "智慧",
                "connect": "關愛",
                "help": "善良",
                "achieve": "勇氣",
                "enjoy": "快樂"
            }
            profile['values']['core'] = [
                mapping.get(a, a) for a in answers[6] if a in mapping
            ]

    def _analyze_interests(self, profile: Dict, answers: Dict):
        """分析興趣"""
        # Q7: 週末活動
        if 7 in answers:
            mapping = {
                "outdoors": "運動",
                "social": "社交",
                "creative": "藝術",
                "learning": "閱讀",
                "relaxing": "娛樂",
                "cooking": "美食"
            }
            profile['interests']['categories'] = [
                mapping.get(a, a) for a in answers[7] if a in mapping
            ]

        # Q9: 音樂/電影/書籍偏好
        if 9 in answers and isinstance(answers[9], dict):
            for key in ['music', 'movies', 'books']:
                if key in answers[9]:
                    profile['interests']['specific'][key] = answers[9][key]

        # Q10: 興趣深度
        if 10 in answers:
            # 願意深入研究 = enthusiast
            profile['interests']['depth'] = 'enthusiast'

    def _analyze_personality(self, profile: Dict, answers: Dict):
        """分析性格"""
        # Q12: 內外向
        if 12 in answers:
            profile['personality']['traits']['introversion'] = int(answers[12])

        # Q11: 社交風格
        if 11 in answers:
            style_mapping = {
                "one_on_one": "傾聽者",
                "small_group": "分享者",
                "party": "引導者",
                "online": "傾聽者",
                "activity": "分享者"
            }
            profile['personality']['socialStyle'] = style_mapping.get(
                answers[11], "傾聽者"
            )

        # Q15: 獨處需求
        if 15 in answers:
            # 高獨處需求 → 更內向
            alone_score = int(answers[15])
            current = profile['personality']['traits']['introversion']
            profile['personality']['traits']['introversion'] = (current + alone_score) // 2

    def _analyze_communication(self, profile: Dict, answers: Dict):
        """分析對話風格"""
        # Q13: 聊天方式
        if 13 in answers:
            topics = []
            if 'deep' in answers[13]:
                topics.append("人生哲學")
                profile['communication_style']['depth'] = 80
            if 'humor' in answers[13]:
                topics.append("日常趣事")
                profile['communication_style']['humor'] = 80
            if 'sharing' in answers[13]:
                topics.append("生活分享")
                profile['communication_style']['emotionality'] = 70
            if 'debate' in answers[13]:
                topics.append("時事觀點")
            if 'support' in answers[13]:
                topics.append("情感支持")
                profile['communication_style']['emotionality'] = 80

            profile['communication_style']['preferredTopics'] = topics

    def _analyze_emotional(self, profile: Dict, answers: Dict):
        """分析情感需求"""
        # Q14: 愛的語言
        if 14 in answers:
            mapping = {
                "words": "肯定的言語",
                "time": "精心時刻",
                "gifts": "禮物",
                "help": "服務",
                "touch": "肢體接觸"
            }
            profile['love_style']['loveLanguage'] = [
                mapping.get(a, a) for a in answers[14] if a in mapping
            ]

            # 根據愛的語言推斷情感需求
            if 'words' in answers[14]:
                profile['emotional_needs']['validation'] = 80
            if 'time' in answers[14]:
                profile['emotional_needs']['companionship'] = 80


# 單例
questionnaire_analyzer = QuestionnaireAnalyzer()
