from rest_framework.response import Response


class AnalyticsPresenter:
    def analytics_success(self):
        return Response({
            'class_performance_trends': [],
            'subject_wise_analysis': [],
            'teacher_effectiveness': [],
            'student_growth_tracking': [],
        }, status=200)
