from rest_framework.response import Response


class ParentHomeworkPresenter:
    def homework_list_success(self, homework):
        results = [
            {
                'id': h.id,
                'subject': {'id': h.subject_id, 'name': h.subject.name},
                'description': h.description,
                'deadline': h.deadline.isoformat() if h.deadline else None,
                'assigned_by': {'id': h.assigned_by_id, 'name': h.assigned_by.name},
            }
            for h in homework
        ]
        return Response({'count': len(results), 'results': results}, status=200)
