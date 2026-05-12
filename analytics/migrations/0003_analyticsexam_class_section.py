from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('analytics', '0002_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='analyticsexam',
            name='academic_class',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='analytics_exams',
                to='core.academicclass',
            ),
        ),
        migrations.AddField(
            model_name='analyticsexam',
            name='section',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='analytics_exams_direct',
                to='core.section',
            ),
        ),
        migrations.AlterField(
            model_name='analyticsexam',
            name='exam_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='analyticsexam',
            name='uploaded_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name='analyticsexam',
            name='analytics_status',
            field=models.CharField(
                choices=[
                    ('CREATED', 'Created'),
                    ('PENDING', 'Pending'),
                    ('RUNNING', 'Running'),
                    ('DONE', 'Done'),
                    ('FAILED', 'Failed'),
                ],
                default='CREATED',
                max_length=10,
            ),
        ),
    ]
