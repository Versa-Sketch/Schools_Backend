from rest_framework.response import Response


class NotificationPresenter:
    def list_success(self, notifications, unread_count):
        results = [
            {
                'id': n.id,
                'type': n.notif_type,
                'title': n.title,
                'body': n.body,
                'data': n.data,
                'is_read': n.is_read,
                'created_at': n.created_at.isoformat(),
            }
            for n in notifications
        ]
        return Response({'count': len(results), 'unread_count': unread_count, 'results': results}, status=200)

    def mark_read_success(self, count):
        return Response({'marked_read': count}, status=200)

    def unread_count_success(self, count):
        return Response({'count': count}, status=200)
