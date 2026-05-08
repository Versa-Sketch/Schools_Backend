from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

from core.models import School, TimeStampedModel
from .constants import NOTIFICATION_TYPE_CHOICES


class Notification(TimeStampedModel):
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
    )
    notif_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPE_CHOICES)
    title = models.CharField(max_length=255)
    body = models.TextField()
    data = models.JSONField(default=dict, encoder=DjangoJSONEncoder)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read'], name='notif_recipient_read_idx'),
            models.Index(fields=['recipient', 'created_at'], name='notif_recipient_created_idx'),
        ]

    def __str__(self):
        return f'{self.notif_type} → {self.recipient}'
