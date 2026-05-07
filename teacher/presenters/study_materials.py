from rest_framework.response import Response


class StudyMaterialsPresenter:
    def study_material_success(self, material):
        return Response({
            'id': material.id,
            'section_id': material.section_id,
            'subject': {'id': material.subject_id, 'name': material.subject.name},
            'title': material.title,
            'description': material.description,
            'material_date': str(material.material_date),
            'file_url': material.file or None,
            'uploaded_by': {'id': material.uploaded_by_id, 'name': material.uploaded_by.name},
        }, status=201)

    def study_material_list_success(self, materials):
        results = [
            {
                'id': m.id,
                'section_id': m.section_id,
                'subject': {'id': m.subject_id, 'name': m.subject.name},
                'title': m.title,
                'description': m.description,
                'material_date': str(m.material_date),
                'file_url': m.file or None,
                'uploaded_by': {'id': m.uploaded_by_id, 'name': m.uploaded_by.name},
            }
            for m in materials
        ]
        return Response({'count': len(results), 'results': results}, status=200)
