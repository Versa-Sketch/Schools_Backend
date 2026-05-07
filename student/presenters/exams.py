from rest_framework.response import Response
from core import constants as core_constants


class StudentExamPresenter:
    def exam_not_implemented(self):
        return Response({
            'success': False,
            'code': core_constants.EXAM_MODEL_NOT_IMPLEMENTED,
            'details': 'Exam management models are not yet implemented.',
        }, status=501)
