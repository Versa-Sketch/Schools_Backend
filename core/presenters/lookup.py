from rest_framework.response import Response


class LookupPresenter:
    def class_list_success(self, classes):
        results = [
            {'id': c.id, 'name': c.name, 'display_order': c.display_order}
            for c in classes
        ]
        return Response({'count': len(results), 'results': results}, status=200)

    def section_list_success(self, sections):
        results = [
            {
                'id': s.id,
                'name': s.name,
                'academic_class': {'id': s.academic_class_id, 'name': s.academic_class.name},
                'class_teacher': (
                    {'id': s.class_teacher_id, 'name': s.class_teacher.name}
                    if s.class_teacher_id else None
                ),
            }
            for s in sections
        ]
        return Response({'count': len(results), 'results': results}, status=200)

    def student_list_success(self, students):
        results = [self._fmt_student(s) for s in students]
        return Response({'count': len(results), 'results': results}, status=200)

    def student_detail_success(self, student, date, attendance_records):
        return Response({
            'student': self._fmt_student(student),
            'attendance': self._fmt_day_attendance(date, attendance_records),
        }, status=200)

    def subject_list_success(self, subjects):
        results = [
            {'id': s.id, 'name': s.name, 'code': s.code, 'is_active': s.is_active}
            for s in subjects
        ]
        return Response({'count': len(results), 'results': results}, status=200)

    def _fmt_student(self, student):
        return {
            'id': student.id,
            'user_id': student.user_id,
            'name': student.name,
            'roll_number': student.roll_number,
            'admission_number': student.admission_number,
            'academic_class': {
                'id': student.academic_class_id,
                'name': student.academic_class.name,
            },
            'section': {
                'id': student.section_id,
                'name': student.section.name,
            },
        }

    def _fmt_day_attendance(self, date, attendance_records):
        records = list(attendance_records)
        present_count = sum(1 for r in records if r.status == 'PRESENT')
        absent_count = sum(1 for r in records if r.status == 'ABSENT')

        if not records:
            status = 'NOT_MARKED'
        elif present_count and absent_count:
            status = 'PARTIAL'
        elif present_count:
            status = 'PRESENT'
        else:
            status = 'ABSENT'

        return {
            'date': str(date),
            'status': status,
            'present_count': present_count,
            'absent_count': absent_count,
            'records': [
                {
                    'slot': r.session.slot,
                    'status': r.status,
                    'confirmed_at': r.session.confirmed_at.isoformat() if r.session.confirmed_at else None,
                }
                for r in records
            ],
        }
