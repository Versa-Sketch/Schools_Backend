from rest_framework.response import Response


class StudentHomeworkPresenter:
    def _fmt_attachments(self, homework):
        return [
            {
                'url': a.file,
                'filename': a.filename,
                'content_type': a.content_type,
            }
            for a in homework.attachments.all()
        ]

    def homework_list_success(self, homework):
        results = [
            {
                'id': h.id,
                'subject': {'id': h.subject_id, 'name': h.subject.name},
                'description': h.description,
                'deadline': h.deadline.isoformat() if h.deadline else None,
                'assigned_by': {'id': h.assigned_by_id, 'name': h.assigned_by.name},
                'attachments': self._fmt_attachments(h),
            }
            for h in homework
        ]
        return Response({'count': len(results), 'results': results}, status=200)
