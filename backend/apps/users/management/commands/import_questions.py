"""
匯入預設問卷問題
Import default questionnaire questions
"""

from django.core.management.base import BaseCommand
from apps.users.models import Question, QuestionOption


class Command(BaseCommand):
    help = '匯入預設的 15 題問卷'

    def handle(self, *args, **options):
        questions_data = [
            # === 三觀問題 (6題) ===
            {
                "order": 1,
                "category": "lifeview",
                "question_type": "multiple_choice",
                "question_text": "你認為人生最重要的是什麼？",
                "allow_multiple": True,
                "max_selections": 2,
                "options": [
                    {"value": "happiness", "label": "追求快樂和享受生活"},
                    {"value": "achievement", "label": "實現自我和達成目標"},
                    {"value": "helping", "label": "幫助他人和貢獻社會"},
                    {"value": "experience", "label": "體驗世界和拓展視野"},
                    {"value": "connection", "label": "建立深厚的人際關係"},
                ],
            },
            {
                "order": 2,
                "category": "worldview",
                "question_type": "scale",
                "question_text": "面對困難時，你通常會怎麼想？",
                "scale_left_label": "事情總會變好的",
                "scale_right_label": "需要務實面對現實",
                "analysis_field": "optimism",
            },
            {
                "order": 3,
                "category": "worldview",
                "question_type": "scale",
                "question_text": "你更重視個人成就還是群體和諧？",
                "scale_left_label": "個人成就和獨立",
                "scale_right_label": "群體和諧與團隊",
                "analysis_field": "individualism",
            },
            {
                "order": 4,
                "category": "values",
                "question_type": "multiple_choice",
                "question_text": "對你來說，什麼是絕對不能接受的？（可多選）",
                "allow_multiple": True,
                "max_selections": 3,
                "analysis_field": "dealbreakers",
                "options": [
                    {"value": "dishonesty", "label": "欺騙和不誠實"},
                    {"value": "coldness", "label": "冷漠和缺乏同理心"},
                    {"value": "arrogance", "label": "傲慢和瞧不起人"},
                    {"value": "laziness", "label": "懶惰和不負責任"},
                    {"value": "control", "label": "控制慾強和不尊重"},
                    {"value": "superficial", "label": "膚淺和只看外表"},
                ],
            },
            {
                "order": 5,
                "category": "lifeview",
                "question_type": "single_choice",
                "question_text": "你現在人生階段的首要目標是什麼？",
                "analysis_field": "lifeStage",
                "options": [
                    {"value": "explore", "label": "探索自我，找到方向"},
                    {"value": "career", "label": "事業發展，追求成就"},
                    {"value": "stability", "label": "穩定生活，平衡各方面"},
                    {"value": "relationship", "label": "找到伴侶，建立家庭"},
                    {"value": "enjoy", "label": "享受生活，追求體驗"},
                ],
            },
            {
                "order": 6,
                "category": "values",
                "question_type": "multiple_choice",
                "question_text": "什麼事情會讓你感到生活有意義？（可多選）",
                "allow_multiple": True,
                "max_selections": 3,
                "analysis_field": "core_values",
                "options": [
                    {"value": "create", "label": "創造新事物"},
                    {"value": "learn", "label": "學習新知識"},
                    {"value": "connect", "label": "與人深度連結"},
                    {"value": "help", "label": "幫助他人"},
                    {"value": "achieve", "label": "達成目標"},
                    {"value": "enjoy", "label": "享受當下"},
                ],
            },

            # === 興趣問題 (5題) ===
            {
                "order": 7,
                "category": "interests",
                "question_type": "multiple_choice",
                "question_text": "週末你最想做什麼？",
                "allow_multiple": True,
                "max_selections": 2,
                "options": [
                    {"value": "outdoors", "label": "戶外活動（運動、旅行、露營）"},
                    {"value": "social", "label": "社交活動（聚會、約會、聊天）"},
                    {"value": "creative", "label": "創作活動（繪畫、音樂、寫作）"},
                    {"value": "learning", "label": "學習活動（閱讀、上課、研究）"},
                    {"value": "relaxing", "label": "放鬆活動（追劇、遊戲、發呆）"},
                    {"value": "cooking", "label": "美食活動（烹飪、探店、品嚐）"},
                ],
            },
            {
                "order": 8,
                "category": "interests",
                "question_type": "text",
                "question_text": "最近讓你興奮或感興趣的話題是什麼？",
                "placeholder": "例如：AI 技術、某部電影、某個哲學問題...",
            },
            {
                "order": 9,
                "category": "interests",
                "question_type": "tags",
                "question_text": "你偏好什麼類型的音樂/電影/書籍？",
                "allow_multiple": True,
                "max_selections": 9,
                "options": [
                    # 音樂
                    {"value": "music_pop", "label": "流行音樂"},
                    {"value": "music_indie", "label": "獨立音樂"},
                    {"value": "music_classical", "label": "古典音樂"},
                    {"value": "music_electronic", "label": "電子音樂"},
                    {"value": "music_hiphop", "label": "嘻哈"},
                    {"value": "music_rock", "label": "搖滾"},
                    # 電影
                    {"value": "movie_romance", "label": "愛情片"},
                    {"value": "movie_scifi", "label": "科幻片"},
                    {"value": "movie_documentary", "label": "紀錄片"},
                    {"value": "movie_comedy", "label": "喜劇"},
                    {"value": "movie_action", "label": "動作片"},
                    {"value": "movie_animation", "label": "動畫"},
                    # 書籍
                    {"value": "book_fiction", "label": "小說"},
                    {"value": "book_psychology", "label": "心理學"},
                    {"value": "book_philosophy", "label": "哲學"},
                    {"value": "book_business", "label": "商業"},
                    {"value": "book_science", "label": "科普"},
                ],
            },
            {
                "order": 10,
                "category": "interests",
                "question_type": "single_choice",
                "question_text": "你願意花時間深入研究的領域是？",
                "analysis_field": "interest_depth",
                "options": [
                    {"value": "tech", "label": "科技與創新"},
                    {"value": "art", "label": "藝術與設計"},
                    {"value": "nature", "label": "自然與環境"},
                    {"value": "psychology", "label": "心理與人性"},
                    {"value": "business", "label": "商業與經濟"},
                    {"value": "culture", "label": "文化與歷史"},
                    {"value": "fitness", "label": "健身與運動"},
                ],
            },
            {
                "order": 11,
                "category": "interests",
                "question_type": "single_choice",
                "question_text": "你理想的社交活動是什麼？",
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
                "order": 12,
                "category": "personality",
                "question_type": "scale",
                "question_text": "在聚會中，你通常是...？",
                "scale_left_label": "主動找人聊天，認識新朋友",
                "scale_right_label": "等待別人來找我，或和熟人待在一起",
                "analysis_field": "introversion",
            },
            {
                "order": 13,
                "category": "communication",
                "question_type": "multiple_choice",
                "question_text": "你喜歡的聊天方式是...？",
                "allow_multiple": True,
                "max_selections": 2,
                "options": [
                    {"value": "deep", "label": "深度話題（人生、哲學、夢想）"},
                    {"value": "humor", "label": "輕鬆幽默（開玩笑、吐槽）"},
                    {"value": "sharing", "label": "互相分享（日常、感受）"},
                    {"value": "debate", "label": "觀點討論（時事、看法）"},
                    {"value": "support", "label": "傾聽支持（陪伴、安慰）"},
                ],
            },
            {
                "order": 14,
                "category": "emotional",
                "question_type": "multiple_choice",
                "question_text": "什麼讓你感到被理解和被關心？",
                "allow_multiple": True,
                "max_selections": 2,
                "analysis_field": "love_language",
                "options": [
                    {"value": "words", "label": "聽到肯定和鼓勵的話"},
                    {"value": "time", "label": "對方花時間陪伴我"},
                    {"value": "gifts", "label": "收到貼心的禮物"},
                    {"value": "help", "label": "對方主動幫助我"},
                    {"value": "touch", "label": "肢體上的親密接觸"},
                ],
            },
            {
                "order": 15,
                "category": "personality",
                "question_type": "scale",
                "question_text": "你需要多少獨處時間？",
                "scale_left_label": "不太需要，喜歡和人在一起",
                "scale_right_label": "很需要，經常需要獨處充電",
                "analysis_field": "alone_time_need",
            },
        ]

        created_count = 0
        for q_data in questions_data:
            options = q_data.pop('options', [])

            question, created = Question.objects.update_or_create(
                order=q_data['order'],
                defaults=q_data
            )

            if created:
                created_count += 1

            # 建立選項
            for i, opt in enumerate(options):
                QuestionOption.objects.update_or_create(
                    question=question,
                    value=opt['value'],
                    defaults={
                        'label': opt['label'],
                        'order': i,
                    }
                )

        self.stdout.write(
            self.style.SUCCESS(f'成功匯入 {created_count} 題新問題，共 {len(questions_data)} 題')
        )
