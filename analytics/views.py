import io

from django.conf import settings
from django.http import HttpResponse
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from rest_framework.parsers import JSONParser

from core.permissions import IsAdmin, IsPrincipal, IsParent, IsStudent, IsTeacher
from analytics.interactors.dashboard import DashboardInteractor
from analytics.interactors.exams import (
    CreateExamInteractor,
    ExamOverviewInteractor,
    ListExamsInteractor,
    ClassSubjectQuestionsInteractor,
    ClassQuestionStudentsInteractor,
    SectionDetailInteractor,
    SectionSubjectQuestionsInteractor,
    SectionQuestionStudentsInteractor,
)
from analytics.interactors.section import SectionInteractor
from analytics.interactors.student import StudentInteractor
from analytics.interactors.upload import UploadExamCSVInteractor
from analytics.presenters.dashboard import DashboardPresenter
from analytics.presenters.exams import ExamPresenter
from analytics.presenters.section import SectionPresenter
from analytics.presenters.student import StudentPresenter
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


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def exams_view(request):
    if request.method == 'POST':
        if request.user.role not in ('PRINCIPAL', 'ADMIN'):
            return Response({'success': False, 'details': 'Permission denied.'}, status=403)
        return CreateExamInteractor(
            storage=AnalyticsDB(), presenter=ExamPresenter(),
        ).create(user=request.user, data=request.data)
        
    return ListExamsInteractor(
        storage=AnalyticsDB(), presenter=ExamPresenter(),
    ).list(user=request.user)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsPrincipal | IsAdmin])
@parser_classes([MultiPartParser, FormParser])
def upload_exam_view(request, exam_id):
    return UploadExamCSVInteractor(
        storage=AnalyticsDB(), presenter=UploadPresenter(),
    ).upload(
        user=request.user,
        exam_id=exam_id,
        csv_file=request.FILES.get('csv_file'),
        excel_file=request.FILES.get('excel_file'),
        pdf_file=request.FILES.get('pdf_file'),
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def exam_overview_view(request, exam_id):
    return ExamOverviewInteractor(
        storage=AnalyticsDB(), presenter=ExamPresenter(),
    ).overview(user=request.user, exam_id=exam_id)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsPrincipal | IsAdmin])
def class_subject_questions_view(request, exam_id, subject_id):
    return ClassSubjectQuestionsInteractor(
        storage=AnalyticsDB(), presenter=ExamPresenter(),
    ).get(user=request.user, exam_id=exam_id, subject_id=subject_id)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsPrincipal | IsAdmin])
def class_question_students_view(request, exam_id, subject_id, q_no):
    return ClassQuestionStudentsInteractor(
        storage=AnalyticsDB(), presenter=ExamPresenter(),
    ).get(user=request.user, exam_id=exam_id, subject_id=subject_id, q_no=q_no)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsPrincipal | IsAdmin])
def section_detail_view(request, exam_id, section_id):
    return SectionDetailInteractor(
        storage=AnalyticsDB(), presenter=SectionPresenter(),
    ).get(user=request.user, exam_id=exam_id, section_id=section_id)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsPrincipal | IsAdmin])
def section_subject_questions_view(request, exam_id, section_id, subject_id):
    return SectionSubjectQuestionsInteractor(
        storage=AnalyticsDB(), presenter=SectionPresenter(),
    ).get(user=request.user, exam_id=exam_id, section_id=section_id, subject_id=subject_id)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsPrincipal | IsAdmin])
def section_question_students_view(request, exam_id, section_id, subject_id, q_no):
    return SectionQuestionStudentsInteractor(
        storage=AnalyticsDB(), presenter=SectionPresenter(),
    ).get(
        user=request.user,
        exam_id=exam_id,
        section_id=section_id,
        subject_id=subject_id,
        q_no=q_no,
    )


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
def class_detail_view(request, class_id):
    return DashboardInteractor(
        storage=AnalyticsDB(),
        presenter=DashboardPresenter(),
    ).get_class_detail(
        user=request.user,
        class_id=class_id,
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
def question_heatmap_view(request, section_id, subject_id):
    return SectionInteractor(
        storage=AnalyticsDB(),
        presenter=SectionPresenter(),
    ).get_question_heatmap(
        user=request.user,
        section_id=section_id,
        subject_id=subject_id,
        exam_id=request.query_params.get('exam_id'),
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsPrincipal | IsAdmin | IsTeacher])
def question_detail_view(request, section_id, subject_id, q_no):
    return SectionInteractor(
        storage=AnalyticsDB(),
        presenter=SectionPresenter(),
    ).get_question_detail(
        user=request.user,
        section_id=section_id,
        subject_id=subject_id,
        q_no=q_no,
        exam_id=request.query_params.get('exam_id'),
    )


# ---------------------------------------------------------------- 7c Student Screens

@api_view(['GET'])
@permission_classes([
    IsAuthenticated,
    IsPrincipal | IsAdmin | IsTeacher | IsStudent | IsParent,
])
def student_all_exams_view(request, student_id):
    return StudentInteractor(
        storage=AnalyticsDB(),
        presenter=StudentPresenter(),
    ).get_student_all_exams(
        user=request.user,
        student_id=student_id,
    )


@api_view(['GET'])
@permission_classes([
    IsAuthenticated,
    IsPrincipal | IsAdmin | IsTeacher | IsStudent | IsParent,
])
def student_summary_view(request, student_id):
    return StudentInteractor(
        storage=AnalyticsDB(),
        presenter=StudentPresenter(),
    ).get_student_summary(
        user=request.user,
        student_id=student_id,
        exam_id=request.query_params.get('exam_id'),
    )


@api_view(['GET'])
@permission_classes([
    IsAuthenticated,
    IsPrincipal | IsAdmin | IsTeacher | IsStudent | IsParent,
])
def student_subject_view(request, student_id, subject_id):
    return StudentInteractor(
        storage=AnalyticsDB(),
        presenter=StudentPresenter(),
    ).get_student_subject(
        user=request.user,
        student_id=student_id,
        subject_id=subject_id,
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
