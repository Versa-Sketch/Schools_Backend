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

    def subject_list_success(self, subjects):
        results = [
            {'id': s.id, 'name': s.name, 'code': s.code, 'is_active': s.is_active}
            for s in subjects
        ]
        return Response({'count': len(results), 'results': results}, status=200)
