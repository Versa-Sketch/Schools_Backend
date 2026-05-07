from rest_framework.response import Response


class CalendarPresenter:
    def calendar_event_success(self, event):
        return Response({
            'id': event.id,
            'title': event.title,
            'event_type': event.event_type,
            'start_date': str(event.start_date),
            'end_date': str(event.end_date),
            'description': event.description,
            'visible_to': event.visible_to,
        }, status=201)
