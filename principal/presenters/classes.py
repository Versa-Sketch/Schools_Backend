from rest_framework.response import Response


class ClassesPresenter:
    def class_success(self, academic_class):
        return Response({
            'id': academic_class.id,
            'name': academic_class.name,
            'display_order': academic_class.display_order,
        }, status=200)

    def class_created(self, academic_class):
        return Response({
            'id': academic_class.id,
            'name': academic_class.name,
            'display_order': academic_class.display_order,
        }, status=201)

    def class_deleted(self):
        return Response({'success': True, 'message': 'Class deleted successfully.'}, status=200)
