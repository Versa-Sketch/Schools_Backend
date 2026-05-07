from rest_framework.response import Response


class ParentAttendancePresenter:
    def attendance_success(self, records):
        records_list = list(records)
        present = sum(1 for r in records_list if r.status == 'PRESENT')
        absent = sum(1 for r in records_list if r.status == 'ABSENT')
        total = present + absent
        percentage = round((present / total) * 100, 1) if total > 0 else 0.0
        results = [
            {
                'date': str(r.session.date),
                'slot': r.session.slot,
                'status': r.status,
                'confirmed_at': r.session.confirmed_at.isoformat() if r.session.confirmed_at else None,
            }
            for r in records_list
        ]
        return Response({
            'count': len(results),
            'results': results,
            'summary': {'present_count': present, 'absent_count': absent, 'attendance_percentage': percentage},
        }, status=200)
