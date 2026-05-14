# Generated manually because local Django startup is blocked by missing pdfplumber.

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_school_logo'),
    ]

    operations = [
        migrations.CreateModel(
            name='HomeworkAttachment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('file', models.URLField(max_length=500)),
                ('filename', models.CharField(max_length=255)),
                ('content_type', models.CharField(max_length=100)),
                ('homework', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attachments', to='core.homework')),
            ],
        ),
    ]
