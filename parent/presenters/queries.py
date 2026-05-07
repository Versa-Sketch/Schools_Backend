from rest_framework.response import Response


class ParentQueriesPresenter:
    def query_detail_success(self, query):
        return Response({
            'id': query.id,
            'student': {'id': query.student_id, 'name': query.student.name},
            'section_id': query.section_id,
            'assigned_teacher': {'id': query.assigned_teacher_id, 'name': query.assigned_teacher.name},
            'subject': query.subject,
            'message': query.message,
            'status': query.status,
            'created_at': query.created_at.isoformat(),
        }, status=201)

    def query_list_success(self, queries):
        results = [
            {
                'id': q.id,
                'subject': q.subject,
                'status': q.status,
                'student': {'id': q.student_id, 'name': q.student.name},
                'assigned_teacher': {'id': q.assigned_teacher_id, 'name': q.assigned_teacher.name},
                'created_at': q.created_at.isoformat(),
            }
            for q in queries
        ]
        return Response({'count': len(results), 'results': results}, status=200)

    def query_with_replies_success(self, query):
        return Response({
            'id': query.id,
            'subject': query.subject,
            'message': query.message,
            'status': query.status,
            'student': {'id': query.student_id, 'name': query.student.name},
            'assigned_teacher': {'id': query.assigned_teacher_id, 'name': query.assigned_teacher.name},
            'replies': [
                {
                    'id': r.id,
                    'sender_id': r.sender_id,
                    'sender_role': r.sender.role,
                    'message': r.message,
                    'created_at': r.created_at.isoformat(),
                }
                for r in query.parentqueryreply_set.all()
            ],
        }, status=200)

    def reply_success(self, reply):
        return Response({
            'id': reply.id,
            'query_id': reply.query_id,
            'sender_id': reply.sender_id,
            'message': reply.message,
            'created_at': reply.created_at.isoformat(),
        }, status=201)
