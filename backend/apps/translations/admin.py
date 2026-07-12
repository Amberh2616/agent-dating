from django.contrib import admin
from .models import TranslationCategory, TranslationKey, TranslationValue


class TranslationValueInline(admin.TabularInline):
    model = TranslationValue
    extra = 3
    fields = ['language', 'text', 'is_verified', 'translator']


@admin.register(TranslationCategory)
class TranslationCategoryAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'name', 'app_name', 'key_count')
    list_filter = ('app_name',)
    search_fields = ('name', 'display_name')

    def key_count(self, obj):
        return obj.keys.count()
    key_count.short_description = '翻譯數量'


@admin.register(TranslationKey)
class TranslationKeyAdmin(admin.ModelAdmin):
    list_display = ('key', 'category', 'default_text_preview', 'translation_count')
    list_filter = ('category', 'category__app_name')
    search_fields = ('key', 'default_text', 'description')
    inlines = [TranslationValueInline]

    fieldsets = (
        ('基本資訊', {
            'fields': ('category', 'key', 'description')
        }),
        ('預設文字（繁體中文）', {
            'fields': ('default_text',)
        }),
    )

    def default_text_preview(self, obj):
        text = obj.default_text
        return text[:50] + '...' if len(text) > 50 else text
    default_text_preview.short_description = '預設文字'

    def translation_count(self, obj):
        return obj.translations.count()
    translation_count.short_description = '已翻譯'
