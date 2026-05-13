from rest_framework.response import Response


def _format_section(section):
    return {
        'id': section.id,
        'name': section.name,
        'academic_class': {
            'id': section.academic_class_id,
            'name': section.academic_class.name,
        },
        'class_teacher': (
            {'id': section.class_teacher_id, 'name': section.class_teacher.name}
            if section.class_teacher_id else None
        ),
        'parent_query_enabled': section.parent_query_enabled,
    }


class SectionsPresenter:
    def section_list_success(self, sections):
        results = [_format_section(s) for s in sections]
        return Response({'count': len(results), 'results': results}, status=200)

    def section_detail_success(self, section):
        return Response(_format_section(section), status=200)

    def section_created(self, section):
        return Response(_format_section(section), status=201)

    def section_deleted(self):
        return Response({'success': True, 'message': 'Section deleted successfully.'}, status=200)
