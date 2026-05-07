from rest_framework.response import Response


class HomeworkPresenter:
    def homework_success(self, homework):
        return Response({
            'id': homework.id,
            'section_id': homework.section_id,
            'subject': {'id': homework.subject_id, 'name': homework.subject.name},
            'description': homework.description,
            'deadline': homework.deadline.isoformat() if homework.deadline else None,
        }, status=201)

    def homework_list_success(self, homework):
        results = [
            {
                'id': h.id,
                'section_id': h.section_id,
                'subject': {'id': h.subject_id, 'name': h.subject.name},
                'description': h.description,
                'deadline': h.deadline.isoformat() if h.deadline else None,
            }
            for h in homework
        ]
        return Response({'count': len(results), 'results': results}, status=200)
