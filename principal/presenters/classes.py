from rest_framework.response import Response


class ClassesPresenter:
    def class_success(self, academic_class):
        return Response({
            'id': academic_class.id,
            'name': academic_class.name,
            'display_order': academic_class.display_order,
        }, status=200)

    def class_list_success(self, classes):
        return Response({
            'count': len(classes),
            'results': [
                {
                    'id': cls.id,
                    'name': cls.name,
                    'display_order': cls.display_order,
                }
                for cls in classes
            ]
        }, status=200)

    def class_created(self, academic_class):
        return Response({
            'id': academic_class.id,
            'name': academic_class.name,
            'display_order': academic_class.display_order,
        }, status=201)

    def class_deleted(self):
        return Response({'success': True, 'message': 'Class deleted successfully.'}, status=200)
