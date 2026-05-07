from django.utils import timezone

from notifications.models import Notification


class NotificationDB:
    def get_notifications_for_user(self, user, unread_only=False):
        qs = Notification.objects.filter(recipient=user)
        if unread_only:
            qs = qs.filter(is_read=False)
        return qs

    def get_unread_count(self, user):
        return Notification.objects.filter(recipient=user, is_read=False).count()

    def mark_as_read(self, user, notification_ids=None):
        qs = Notification.objects.filter(recipient=user, is_read=False)
        if notification_ids:
            qs = qs.filter(id__in=notification_ids)
        return qs.update(is_read=True, read_at=timezone.now())
