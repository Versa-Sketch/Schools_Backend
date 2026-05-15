from rest_framework.response import Response


class AssignSectionsPresenter:
    def assign_success(self, teacher):
        return Response({
            'message': 'Sections and subject assigned successfully.',
            'teacher_id': teacher.id,
            'primary_subject': {
                'id': teacher.primary_subject.id,
                'name': teacher.primary_subject.name,
            } if teacher.primary_subject else None,
            'assigned_sections': [
                {
                    'id': s.id,
                    'name': s.name,
                    'class': s.academic_class.name,
                }
                for s in teacher.assigned_sections.select_related('academic_class').all()
            ],
        }, status=200)
