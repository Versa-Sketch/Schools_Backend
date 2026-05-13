from rest_framework.response import Response


class SubjectsPresenter:
    def subject_success(self, subject):
        return Response({
            'id': subject.id,
            'name': subject.name,
            'code': subject.code,
            'is_active': subject.is_active,
        }, status=200)

    def subject_created(self, subject):
        return Response({
            'id': subject.id,
            'name': subject.name,
            'code': subject.code,
            'is_active': subject.is_active,
        }, status=201)

    def subject_deleted(self):
        return Response({'success': True, 'message': 'Subject deleted successfully.'}, status=200)
