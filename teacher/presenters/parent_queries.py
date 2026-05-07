from rest_framework.response import Response


class ParentQueriesPresenter:
    def query_list_success(self, queries):
        results = [
            {
                'id': q.id,
                'subject': q.subject,
                'message': q.message,
                'status': q.status,
                'parent': {'id': q.parent_id, 'name': q.parent.name},
                'student': {'id': q.student_id, 'name': q.student.name},
                'section_id': q.section_id,
                'created_at': q.created_at.isoformat(),
            }
            for q in queries
        ]
        return Response({'count': len(results), 'results': results}, status=200)

    def reply_success(self, reply, query):
        return Response({
            'id': reply.id,
            'query_id': reply.query_id,
            'sender_id': reply.sender_id,
            'message': reply.message,
            'query_status': query.status,
            'created_at': reply.created_at.isoformat(),
        }, status=201)
