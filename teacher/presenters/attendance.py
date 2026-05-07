from rest_framework.response import Response


class AttendancePresenter:
    def attendance_session_success(self, session, records):
        return Response({
            'id': session.id,
            'section_id': session.section_id,
            'date': str(session.date),
            'slot': session.slot,
            'taken_by': {'id': session.taken_by_id, 'name': session.taken_by.name},
            'confirmed_at': session.confirmed_at.isoformat() if session.confirmed_at else None,
            'records': [
                {'student_id': r.student_id, 'student_name': r.student.name, 'status': r.status}
                for r in records
            ],
        }, status=200)

    def attendance_records_success(self, session_id, records):
        return Response({
            'session_id': session_id,
            'records': [
                {'student_id': r.student_id, 'student_name': r.student.name, 'status': r.status}
                for r in records
            ],
        }, status=200)

    def confirm_success(self, session, absent_count, notification_count):
        return Response({
            'session_id': session.id,
            'confirmed_at': session.confirmed_at.isoformat() if session.confirmed_at else None,
            'absent_count': absent_count,
            'notification_logs_created': notification_count,
        }, status=200)
