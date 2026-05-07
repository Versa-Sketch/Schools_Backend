from rest_framework.response import Response


class ParentStudyMaterialsPresenter:
    def study_material_list_success(self, materials):
        results = [
            {
                'id': m.id,
                'title': m.title,
                'description': m.description,
                'subject': {'id': m.subject_id, 'name': m.subject.name},
                'material_date': str(m.material_date),
                'file_url': m.file or None,
                'uploaded_by': {'id': m.uploaded_by_id, 'name': m.uploaded_by.name},
            }
            for m in materials
        ]
        return Response({'count': len(results), 'results': results}, status=200)
