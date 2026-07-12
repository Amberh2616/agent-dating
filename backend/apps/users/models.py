"""
用戶與靈魂檔案模型
User and Soul Profile Models
"""

import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """自定義用戶模型"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    avatar_url = models.URLField(blank=True, null=True)
    bio = models.TextField(blank=True, null=True, max_length=500)
    gender = models.CharField(max_length=20, blank=True, null=True)
    birthday = models.DateField(blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)

    # 語言偏好
    preferred_language = models.CharField(
        max_length=20,
        default='zh-hant',
        help_text='用戶偏好語言（如 zh-hant, en, es, ja）'
    )

    # 帳號狀態
    is_verified = models.BooleanField(default=False)
    is_premium = models.BooleanField(default=False)
    onboarding_completed = models.BooleanField(default=False)

    # 時間戳
    last_active = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users'
        verbose_name = '用戶'
        verbose_name_plural = '用戶'

    def __str__(self):
        return self.email


class SoulProfile(models.Model):
    """
    靈魂檔案 - 用戶的深層特質分析
    Soul Profile - Deep personality analysis for matching
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='soul_profile')

    # ========== 三觀 (核心) ==========

    # 世界觀 - 如何看待世界
    worldview = models.JSONField(default=dict, help_text='''
        {
            "optimism": 0-100,        # 悲觀←→樂觀
            "spirituality": 0-100,    # 唯物←→唯心
            "individualism": 0-100,   # 集體←→個人主義
            "changeOriented": 0-100   # 傳統←→求變
        }
    ''')

    # 人生觀 - 人生意義與目標
    lifeview = models.JSONField(default=dict, help_text='''
        {
            "purpose": ["追求快樂", "實現自我", "幫助他人", "創造價值"],
            "priorities": ["家庭", "事業", "自由", "愛情", "健康"],
            "lifeStage": "探索期" | "奮鬥期" | "穩定期" | "享受期"
        }
    ''')

    # 價值觀 - 核心信念
    values = models.JSONField(default=dict, help_text='''
        {
            "core": ["誠實", "創意", "勇氣", "善良", "智慧"],
            "dealbreakers": ["欺騙", "冷漠"],
            "importanceRank": {
                "love": 1-5,
                "friendship": 1-5,
                "career": 1-5,
                "freedom": 1-5,
                "security": 1-5
            }
        }
    ''')

    # ========== 興趣喜好 ==========

    interests = models.JSONField(default=dict, help_text='''
        {
            "categories": ["藝術", "科技", "運動", "美食", "旅行", "音樂", "閱讀"],
            "specific": {
                "music": ["獨立音樂", "古典", "電子"],
                "movies": ["文藝片", "科幻", "紀錄片"],
                "books": ["心理學", "小說", "哲學"],
                "hobbies": ["攝影", "烹飪", "園藝", "遊戲"]
            },
            "depth": "casual" | "enthusiast" | "expert"
        }
    ''')

    # ========== 性格特質 ==========

    personality = models.JSONField(default=dict, help_text='''
        {
            "mbti": "INFP" | "ENTJ" | ...,
            "traits": {
                "introversion": 0-100,  # 內向←→外向
                "intuition": 0-100,     # 感覺←→直覺
                "thinking": 0-100,      # 情感←→思考
                "judging": 0-100        # 知覺←→判斷
            },
            "socialStyle": "傾聽者" | "分享者" | "引導者"
        }
    ''')

    # ========== 對話與情感 ==========

    communication_style = models.JSONField(default=dict, help_text='''
        {
            "humor": 0-100,            # 幽默程度
            "depth": 0-100,            # 深度 vs 輕鬆
            "emotionality": 0-100,     # 情感表達程度
            "preferredTopics": ["人生哲學", "日常趣事", "專業話題"]
        }
    ''')

    emotional_needs = models.JSONField(default=dict, help_text='''
        {
            "companionship": 0-100,    # 陪伴需求
            "validation": 0-100,       # 被認可需求
            "stimulation": 0-100,      # 刺激/新鮮感需求
            "understanding": 0-100     # 被理解需求
        }
    ''')

    # ========== 戀愛特質 ==========

    love_style = models.JSONField(default=dict, help_text='''
        {
            "attachmentType": "secure" | "anxious" | "avoidant",
            "loveLanguage": ["肯定的言語", "精心時刻", "禮物", "服務", "肢體接觸"],
            "romanticLevel": 0-100,
            "jealousy": 0-100
        }
    ''')

    relationship_behavior = models.JSONField(default=dict, help_text='''
        {
            "initiativeLevel": 0-100,  # 主動程度
            "expressiveness": 0-100,   # 表達愛意程度
            "supportStyle": "傾聽型" | "建議型" | "陪伴型"
        }
    ''')

    # ========== 向量嵌入 (用於配對) ==========

    # 注意: 使用 pgvector 需要安裝擴展
    # soul_vector = VectorField(dimensions=1536)  # OpenAI embedding

    # 替代方案: 使用 JSON 儲存向量
    soul_vector = models.JSONField(default=list, help_text='Soul embedding vector (1536 dimensions)')

    # ========== 元資料 ==========

    questionnaire_completed = models.BooleanField(default=False)
    analysis_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'soul_profiles'
        verbose_name = '靈魂檔案'
        verbose_name_plural = '靈魂檔案'

    def __str__(self):
        return f"{self.user.email} 的靈魂檔案"

    def get_default_worldview(self):
        return {
            'optimism': 50,
            'spirituality': 50,
            'individualism': 50,
            'changeOriented': 50
        }

    def get_default_lifeview(self):
        return {
            'purpose': [],
            'priorities': [],
            'lifeStage': '探索期'
        }

    def get_default_values(self):
        return {
            'core': [],
            'dealbreakers': [],
            'importanceRank': {
                'love': 3,
                'friendship': 3,
                'career': 3,
                'freedom': 3,
                'security': 3
            }
        }


class Question(models.Model):
    """問卷問題"""
    CATEGORY_CHOICES = [
        ('worldview', '世界觀'),
        ('lifeview', '人生觀'),
        ('values', '價值觀'),
        ('interests', '興趣'),
        ('personality', '性格'),
        ('communication', '對話風格'),
        ('emotional', '情感需求'),
    ]

    TYPE_CHOICES = [
        ('single_choice', '單選'),
        ('multiple_choice', '多選'),
        ('scale', '量表'),
        ('text', '文字'),
        ('tags', '標籤'),
    ]

    id = models.AutoField(primary_key=True)
    order = models.IntegerField(default=0, help_text='問題順序')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    question_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='single_choice')

    # 問題內容（多語言）
    question_text = models.TextField(verbose_name='問題內容（繁中）')
    question_text_en = models.TextField(blank=True, verbose_name='問題內容（英文）')
    question_text_ja = models.TextField(blank=True, verbose_name='問題內容（日文）')
    question_text_ko = models.TextField(blank=True, verbose_name='問題內容（韓文）')
    question_text_es = models.TextField(blank=True, verbose_name='問題內容（西班牙文）')
    question_text_fr = models.TextField(blank=True, verbose_name='問題內容（法文）')
    question_text_zh_hans = models.TextField(blank=True, verbose_name='問題內容（簡中）')

    # 選項設定
    allow_multiple = models.BooleanField(default=False, help_text='是否允許多選')
    max_selections = models.IntegerField(default=1, help_text='最多可選幾個')

    # 量表設定（多語言）
    scale_left_label = models.CharField(max_length=100, blank=True, help_text='量表左側標籤（繁中）')
    scale_right_label = models.CharField(max_length=100, blank=True, help_text='量表右側標籤（繁中）')
    scale_left_label_en = models.CharField(max_length=100, blank=True, verbose_name='左側標籤（英文）')
    scale_right_label_en = models.CharField(max_length=100, blank=True, verbose_name='右側標籤（英文）')

    # 分析設定
    analysis_field = models.CharField(max_length=50, blank=True, help_text='對應的靈魂檔案欄位')

    # 文字題設定
    placeholder = models.CharField(max_length=200, blank=True)
    placeholder_en = models.CharField(max_length=200, blank=True, verbose_name='提示文字（英文）')

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_text(self, lang='zh-hant'):
        """取得指定語言的問題文字"""
        lang_map = {
            'en': self.question_text_en,
            'ja': self.question_text_ja,
            'ko': self.question_text_ko,
            'es': self.question_text_es,
            'fr': self.question_text_fr,
            'zh-hans': self.question_text_zh_hans,
        }
        return lang_map.get(lang) or self.question_text

    class Meta:
        db_table = 'questions'
        verbose_name = '問卷問題'
        verbose_name_plural = '問卷問題'
        ordering = ['order']

    def __str__(self):
        return f"Q{self.order}: {self.question_text[:30]}..."


class QuestionOption(models.Model):
    """問題選項"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    value = models.CharField(max_length=50, help_text='選項值')

    # 選項文字（多語言）
    label = models.CharField(max_length=200, help_text='顯示文字（繁中）')
    label_en = models.CharField(max_length=200, blank=True, verbose_name='英文')
    label_ja = models.CharField(max_length=200, blank=True, verbose_name='日文')
    label_ko = models.CharField(max_length=200, blank=True, verbose_name='韓文')
    label_es = models.CharField(max_length=200, blank=True, verbose_name='西班牙文')
    label_fr = models.CharField(max_length=200, blank=True, verbose_name='法文')
    label_zh_hans = models.CharField(max_length=200, blank=True, verbose_name='簡中')

    order = models.IntegerField(default=0)

    class Meta:
        db_table = 'question_options'
        verbose_name = '問題選項'
        verbose_name_plural = '問題選項'
        ordering = ['order']

    def __str__(self):
        return f"{self.question.id} - {self.label}"

    def get_label(self, lang='zh-hant'):
        """取得指定語言的選項文字"""
        lang_map = {
            'en': self.label_en,
            'ja': self.label_ja,
            'ko': self.label_ko,
            'es': self.label_es,
            'fr': self.label_fr,
            'zh-hans': self.label_zh_hans,
        }
        return lang_map.get(lang) or self.label


class QuestionnaireResponse(models.Model):
    """問卷回應記錄"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='questionnaire_responses')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='responses')
    answer = models.JSONField(help_text='回答內容（可以是字串、列表、數字等）')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'questionnaire_responses'
        verbose_name = '問卷回應'
        verbose_name_plural = '問卷回應'
        unique_together = ['user', 'question']

    def __str__(self):
        return f"{self.user.email} - Q{self.question.order}"
