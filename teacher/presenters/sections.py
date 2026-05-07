from rest_framework.response import Response


class SectionsPresenter:
    def section_list_success(self, sections, class_teacher_section_ids):
        results = [
            {
                'id': s.id,
                'class_name': s.academic_class.name,
                'section_name': s.name,
                'is_class_teacher': s.id in class_teacher_section_ids,
                'student_count': getattr(s, 'active_student_count', 0),
            }
            for s in sections
        ]
        return Response({'count': len(results), 'results': results}, status=200)

    def student_list_success(self, students):
        results = [
            {
                'id': s.id,
                'name': s.name,
                'roll_number': s.roll_number,
                'admission_number': s.admission_number,
            }
            for s in students
        ]
        return Response({'count': len(results), 'results': results}, status=200)
