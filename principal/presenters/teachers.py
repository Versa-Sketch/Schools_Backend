from rest_framework.response import Response


def _format_teacher(teacher):
    return {
        'id': teacher.id,
        'user': {
            'id': teacher.user_id,
            'username': teacher.user.username,
            'role': teacher.user.role,
        },
        'name': teacher.name,
        'phone_number': teacher.user.phone_number,
        'primary_subject': (
            {'id': teacher.primary_subject_id, 'name': teacher.primary_subject.name}
            if teacher.primary_subject_id else None
        ),
        'assigned_sections': [
            {'id': s.id, 'class_name': s.academic_class.name, 'section_name': s.name}
            for s in teacher.assigned_sections.all()
        ],
    }


class TeachersPresenter:
    def teacher_list_success(self, teachers):
        results = [_format_teacher(t) for t in teachers]
        return Response({'count': len(results), 'results': results}, status=200)

    def teacher_detail_success(self, teacher):
        return Response(_format_teacher(teacher), status=200)
