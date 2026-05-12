from rest_framework.response import Response


class CalendarPresenter:
    def calendar_event_success(self, event):
        return Response(self._format(event), status=201)

    def calendar_event_update_success(self, event):
        return Response(self._format(event), status=200)

    def calendar_event_delete_success(self):
        return Response({'success': True, 'message': 'Calendar event deleted successfully.'}, status=200)

    def _format(self, event):
        return {
            'id': event.id,
            'title': event.title,
            'event_type': event.event_type,
            'start_date': str(event.start_date),
            'end_date': str(event.end_date),
            'description': event.description,
            'visible_to': event.visible_to,
        }
