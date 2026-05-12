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

    def close_query_success(self, query):
        return Response({'id': query.id, 'status': query.status}, status=200)

    def query_detail_success(self, query):
        return Response({
            'id': query.id,
            'subject': query.subject,
            'message': query.message,
            'status': query.status,
            'parent': {'id': query.parent_id, 'name': query.parent.name},
            'student': {'id': query.student_id, 'name': query.student.name},
            'section_id': query.section_id,
            'created_at': query.created_at.isoformat(),
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
