from django.utils import timezone
from django.utils.dateparse import parse_date

from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser

from core.permissions import IsAdmin, IsPrincipal
from .storages.principal_storage import PrincipalDB
from .interactors import (
    GetConfigurationInteractor,
    UpdateConfigurationInteractor,
    ListTeachersInteractor,
    CreateTeacherInteractor,
    UpdateTeacherInteractor,
    BulkUploadStudentsInteractor,
    GetBulkUploadStatusInteractor,
    CreateAnnouncementInteractor,
    CreateCalendarEventInteractor,
    ListSectionsInteractor,
    UpdateSectionInteractor,
    DailyAttendanceSummaryInteractor,
    ClassAttendanceDetailInteractor,
)
from .presenters.configuration import ConfigurationPresenter
from .presenters.teachers import TeachersPresenter
from .presenters.bulk_upload import BulkUploadPresenter
from .presenters.announcements import AnnouncementPresenter
from .presenters.calendar import CalendarPresenter
from .presenters.sections import SectionsPresenter
from .presenters.attendance import AttendanceSummaryPresenter


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated, IsPrincipal | IsAdmin])
@parser_classes([JSONParser])
def configuration_view(request):
    if request.method == 'GET':
        return GetConfigurationInteractor(
            storage=PrincipalDB(), presenter=ConfigurationPresenter(),
        ).get_configuration(user=request.user)
    return UpdateConfigurationInteractor(
        storage=PrincipalDB(), presenter=ConfigurationPresenter(),
    ).update_configuration(user=request.user, data=request.data)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, IsPrincipal | IsAdmin])
@parser_classes([JSONParser])
def teacher_list_view(request):
    if request.method == 'POST':
        return CreateTeacherInteractor(
            storage=PrincipalDB(), presenter=TeachersPresenter(),
        ).create_teacher(user=request.user, data=request.data)
    return ListTeachersInteractor(
        storage=PrincipalDB(), presenter=TeachersPresenter(),
    ).list_teachers(
        user=request.user,
        subject_id=request.query_params.get('subject_id'),
        section_id=request.query_params.get('section_id'),
        search=request.query_params.get('search'),
    )


@api_view(['PATCH'])
@permission_classes([IsAuthenticated, IsPrincipal | IsAdmin])
@parser_classes([JSONParser])
def teacher_detail_view(request, teacher_id):
    return UpdateTeacherInteractor(
        storage=PrincipalDB(), presenter=TeachersPresenter(),
    ).update_teacher(user=request.user, teacher_id=teacher_id, data=request.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsPrincipal | IsAdmin])
@parser_classes([MultiPartParser, FormParser])
def bulk_upload_view(request):
    return BulkUploadStudentsInteractor(
        storage=PrincipalDB(), presenter=BulkUploadPresenter(),
    ).bulk_upload(user=request.user, csv_file=request.FILES.get('csv_file'))


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsPrincipal | IsAdmin])
def bulk_upload_status_view(request, batch_id):
    return GetBulkUploadStatusInteractor(
        storage=PrincipalDB(), presenter=BulkUploadPresenter(),
    ).get_status(user=request.user, batch_id=batch_id)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsPrincipal | IsAdmin])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def announcement_create_view(request):
    return CreateAnnouncementInteractor(
        storage=PrincipalDB(), presenter=AnnouncementPresenter(),
    ).create_announcement(user=request.user, data=request.data, files=request.FILES.getlist('attachments'))


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsPrincipal | IsAdmin])
@parser_classes([JSONParser])
def calendar_event_create_view(request):
    return CreateCalendarEventInteractor(
        storage=PrincipalDB(), presenter=CalendarPresenter(),
    ).create_event(user=request.user, data=request.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsPrincipal | IsAdmin])
def section_list_view(request):
    return ListSectionsInteractor(
        storage=PrincipalDB(), presenter=SectionsPresenter(),
    ).list_sections(user=request.user, class_id=request.query_params.get('class_id'))


@api_view(['PATCH'])
@permission_classes([IsAuthenticated, IsPrincipal | IsAdmin])
@parser_classes([JSONParser])
def section_detail_view(request, section_id):
    return UpdateSectionInteractor(
        storage=PrincipalDB(), presenter=SectionsPresenter(),
    ).update_section(user=request.user, section_id=section_id, data=request.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsPrincipal | IsAdmin])
def daily_attendance_summary_view(request):
    date_str = request.query_params.get('date')
    date = parse_date(date_str) if date_str else timezone.now().date()
    if date is None:
        date = timezone.now().date()
    return DailyAttendanceSummaryInteractor(
        storage=PrincipalDB(), presenter=AttendanceSummaryPresenter(),
    ).get_summary(user=request.user, date=date)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsPrincipal | IsAdmin])
def class_attendance_detail_view(request, class_id):
    date_str = request.query_params.get('date')
    date = parse_date(date_str) if date_str else timezone.now().date()
    if date is None:
        date = timezone.now().date()
    return ClassAttendanceDetailInteractor(
        storage=PrincipalDB(), presenter=AttendanceSummaryPresenter(),
    ).get_detail(user=request.user, class_id=class_id, date=date)


