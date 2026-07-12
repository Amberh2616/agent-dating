"""
翻譯管理系統
Translation Management System
"""

import uuid
from django.db import models
from django.conf import settings


class TranslationCategory(models.Model):
    """翻譯分類"""
    name = models.CharField(max_length=50, unique=True)
    display_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    app_name = models.CharField(
        max_length=50,
        blank=True,
        help_text='所屬 App（空白=全域）'
    )

    class Meta:
        db_table = 'translation_categories'
        verbose_name = '翻譯分類'
        verbose_name_plural = '翻譯分類'
        ordering = ['app_name', 'name']

    def __str__(self):
        if self.app_name:
            return f"[{self.app_name}] {self.display_name}"
        return f"[全域] {self.display_name}"


class TranslationKey(models.Model):
    """翻譯鍵值"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(
        TranslationCategory,
        on_delete=models.CASCADE,
        related_name='keys'
    )
    key = models.CharField(max_length=100, help_text='翻譯鍵（如 btn.submit）')
    description = models.CharField(max_length=200, blank=True, help_text='說明這個文字用在哪裡')

    # 預設語言內容（繁中）
    default_text = models.TextField(help_text='預設文字（繁體中文）')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'translation_keys'
        verbose_name = '翻譯鍵'
        verbose_name_plural = '翻譯鍵'
        unique_together = ['category', 'key']
        ordering = ['category', 'key']

    def __str__(self):
        return f"{self.category.name}.{self.key}"

    def get_translation(self, lang_code):
        """取得指定語言的翻譯"""
        try:
            return self.translations.get(language=lang_code).text
        except TranslationValue.DoesNotExist:
            return self.default_text


class TranslationValue(models.Model):
    """翻譯內容"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    translation_key = models.ForeignKey(
        TranslationKey,
        on_delete=models.CASCADE,
        related_name='translations'
    )
    language = models.CharField(max_length=10, help_text='語言代碼（如 en, ja）')
    text = models.TextField(help_text='翻譯文字')

    # 翻譯狀態
    is_verified = models.BooleanField(default=False, help_text='是否已校對')
    translator = models.CharField(max_length=100, blank=True, help_text='翻譯者')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'translation_values'
        verbose_name = '翻譯內容'
        verbose_name_plural = '翻譯內容'
        unique_together = ['translation_key', 'language']

    def __str__(self):
        return f"{self.translation_key} [{self.language}]"


# ========== 語言設定 ==========

SUPPORTED_LANGUAGES = [code for code, name in settings.LANGUAGES]

def get_language_choices():
    """取得語言選項"""
    return settings.LANGUAGES
