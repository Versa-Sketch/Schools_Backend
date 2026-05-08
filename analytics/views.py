import io

from django.conf import settings
from django.http import HttpResponse
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.permissions import IsAdmin, IsPrincipal, IsTeacher
from analytics.interactors.dashboard import DashboardInteractor
from analytics.interactors.section import SectionInteractor
from analytics.interactors.upload import UploadExamCSVInteractor
from analytics.presenters.dashboard import DashboardPresenter
from analytics.presenters.section import SectionPresenter
from analytics.presenters.upload import UploadPresenter
from analytics.services.csv_parser import generate_template_csv
from analytics.services.seed import generate_seed_csv
from analytics.storages.analytics_storage import AnalyticsDB


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def template_download_view(request):
    csv_string = generate_template_csv()
    response = HttpResponse(csv_string, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="analytics_template.csv"'
    return response


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsPrincipal | IsAdmin])
@parser_classes([MultiPartParser, FormParser])
def upload_view(request):
    return UploadExamCSVInteractor(
        storage=AnalyticsDB(),
        presenter=UploadPresenter(),
    ).upload(user=request.user, csv_file=request.FILES.get('csv_file'))


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsPrincipal | IsAdmin])
def exams_list_view(request):
    return DashboardInteractor(
        storage=AnalyticsDB(),
        presenter=DashboardPresenter(),
    ).list_exams(user=request.user)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsPrincipal | IsAdmin])
def dashboard_view(request):
    return DashboardInteractor(
        storage=AnalyticsDB(),
        presenter=DashboardPresenter(),
    ).get_dashboard(user=request.user, exam_id=request.query_params.get('exam_id'))


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsPrincipal | IsAdmin])
def class_detail_view(request, class_name):
    return DashboardInteractor(
        storage=AnalyticsDB(),
        presenter=DashboardPresenter(),
    ).get_class_detail(
        user=request.user,
        class_name=class_name,
        exam_id=request.query_params.get('exam_id'),
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsPrincipal | IsAdmin | IsTeacher])
def section_students_view(request, section_id):
    return SectionInteractor(
        storage=AnalyticsDB(),
        presenter=SectionPresenter(),
    ).get_section_students(
        user=request.user,
        section_id=section_id,
        exam_id=request.query_params.get('exam_id'),
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsPrincipal | IsAdmin | IsTeacher])
def question_heatmap_view(request, section_id, subject_name):
    return SectionInteractor(
        storage=AnalyticsDB(),
        presenter=SectionPresenter(),
    ).get_question_heatmap(
        user=request.user,
        section_id=section_id,
        subject_name=subject_name,
        exam_id=request.query_params.get('exam_id'),
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsPrincipal | IsAdmin | IsTeacher])
def question_detail_view(request, section_id, subject_name, q_no):
    return SectionInteractor(
        storage=AnalyticsDB(),
        presenter=SectionPresenter(),
    ).get_question_detail(
        user=request.user,
        section_id=section_id,
        subject_name=subject_name,
        q_no=q_no,
        exam_id=request.query_params.get('exam_id'),
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsPrincipal | IsAdmin])
def seed_view(request):
    if not settings.DEBUG:
        return Response({'success': False, 'detail': 'Not available in production.'}, status=403)
    csv_file      = io.BytesIO(generate_seed_csv().encode('utf-8'))
    csv_file.name = 'seed_data.csv'
    return UploadExamCSVInteractor(
        storage=AnalyticsDB(),
        presenter=UploadPresenter(),
    ).upload(user=request.user, csv_file=csv_file)
