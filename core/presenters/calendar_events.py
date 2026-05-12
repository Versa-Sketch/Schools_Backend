from datetime import date
from rest_framework.response import Response


class CalendarEventPresenter:
    def calendar_list_success(self, events):
        results = [
            {
                'id': e.id,
                'title': e.title,
                'event_type': e.event_type,
                'start_date': str(e.start_date),
                'end_date': str(e.end_date),
                'description': e.description,
                'visible_to': e.visible_to,
            }
            for e in events
        ]
        return Response({'today': str(date.today()), 'count': len(results), 'results': results}, status=200)
