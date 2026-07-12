from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, SoulProfile, Question, QuestionOption, QuestionnaireResponse


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'username', 'is_active', 'is_staff', 'created_at')
    list_filter = ('is_active', 'is_staff', 'gender')
    search_fields = ('email', 'username')
    ordering = ('-created_at',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('個人資料', {'fields': ('username', 'avatar_url', 'bio', 'gender', 'birthday')}),
        ('狀態', {'fields': ('onboarding_completed',)}),
        ('權限', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2'),
        }),
    )


@admin.register(SoulProfile)
class SoulProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'updated_at')
    search_fields = ('user__email', 'user__display_name')
    readonly_fields = ('created_at', 'updated_at')


class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption
    extra = 4
    ordering = ['order']
    fields = ['order', 'value', 'label', 'label_en', 'label_ja']


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'question_text', 'category', 'question_type', 'is_active')
    list_display_links = ('id', 'question_text')
    list_filter = ('category', 'question_type', 'is_active')
    list_editable = ('order', 'is_active')
    search_fields = ('question_text',)
    ordering = ['order']
    inlines = [QuestionOptionInline]

    fieldsets = (
        ('基本設定', {
            'fields': ('order', 'category', 'question_type', 'is_active')
        }),
        ('問題內容（繁中）', {
            'fields': ('question_text',)
        }),
        ('問題翻譯', {
            'fields': ('question_text_en', 'question_text_ja', 'question_text_ko',
                      'question_text_es', 'question_text_fr', 'question_text_zh_hans'),
            'classes': ('collapse',),
        }),
        ('選項設定', {
            'fields': ('allow_multiple', 'max_selections'),
            'classes': ('collapse',),
        }),
        ('量表設定（繁中）', {
            'fields': ('scale_left_label', 'scale_right_label'),
            'classes': ('collapse',),
        }),
        ('量表翻譯（英文）', {
            'fields': ('scale_left_label_en', 'scale_right_label_en'),
            'classes': ('collapse',),
        }),
        ('其他設定', {
            'fields': ('analysis_field', 'placeholder', 'placeholder_en'),
            'classes': ('collapse',),
        }),
    )


@admin.register(QuestionnaireResponse)
class QuestionnaireResponseAdmin(admin.ModelAdmin):
    list_display = ('user', 'question', 'created_at')
    list_filter = ('question__category',)
    search_fields = ('user__email',)
