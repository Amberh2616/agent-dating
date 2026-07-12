from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_question_placeholder_en_question_question_text_en_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='preferred_language',
            field=models.CharField(
                default='zh-hant',
                help_text='用戶偏好語言（如 zh-hant, en, es, ja）',
                max_length=20
            ),
        ),
    ]
