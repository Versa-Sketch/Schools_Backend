from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser

from core.permissions import IsAdmin, IsStudent
from .storages.student_storage import StudentDB
from .interactors import (
    StudentProfileInteractor,
    StudentAttendanceInteractor,
    StudentAnnouncementsInteractor,
    StudentStudyMaterialsInteractor,
    StudentHomeworkInteractor,
    StudentCalendarInteractor,
    StudentExamNotImplementedInteractor,
    UpdateStudentProfilePicInteractor,
)
from .presenters.profile import StudentProfilePresenter
from .presenters.attendance import StudentAttendancePresenter
from .presenters.announcements import StudentAnnouncementsPresenter
from .presenters.study_materials import StudentStudyMaterialsPresenter
from .presenters.homework import StudentHomeworkPresenter
from .presenters.calendar import StudentCalendarPresenter
from .presenters.exams import StudentExamPresenter
from .presenters.profile_pic import ProfilePicPresenter


@api_view(['PATCH'])
@permission_classes([IsAuthenticated, IsStudent | IsAdmin])
@parser_classes([MultiPartParser, FormParser])
def profile_pic_view(request):
    return UpdateStudentProfilePicInteractor(
        presenter=ProfilePicPresenter(),
    ).update(user=request.user, file=request.FILES.get('profile_pic'))


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsStudent | IsAdmin])
def profile_view(request):
    return StudentProfileInteractor(
        storage=StudentDB(), presenter=StudentProfilePresenter(),
    ).get_profile(user=request.user)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsStudent | IsAdmin])
def attendance_view(request):
    return StudentAttendanceInteractor(
        storage=StudentDB(), presenter=StudentAttendancePresenter(),
    ).get_attendance(
        user=request.user,
        date_from=request.query_params.get('date_from'),
        date_to=request.query_params.get('date_to'),
        slot=request.query_params.get('slot'),
        status=request.query_params.get('status'),
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsStudent | IsAdmin])
def announcements_view(request):
    return StudentAnnouncementsInteractor(
        storage=StudentDB(), presenter=StudentAnnouncementsPresenter(),
    ).get_announcements(
        user=request.user,
        audience=request.query_params.get('audience'),
        published_after=request.query_params.get('published_after'),
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsStudent | IsAdmin])
def study_materials_view(request):
    return StudentStudyMaterialsInteractor(
        storage=StudentDB(), presenter=StudentStudyMaterialsPresenter(),
    ).get_materials(
        user=request.user,
        subject_id=request.query_params.get('subject_id'),
        date_from=request.query_params.get('date_from'),
        date_to=request.query_params.get('date_to'),
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsStudent | IsAdmin])
def homework_view(request):
    return StudentHomeworkInteractor(
        storage=StudentDB(), presenter=StudentHomeworkPresenter(),
    ).get_homework(
        user=request.user,
        subject_id=request.query_params.get('subject_id'),
        deadline_from=request.query_params.get('deadline_from'),
        deadline_to=request.query_params.get('deadline_to'),
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsStudent | IsAdmin])
def calendar_events_view(request):
    return StudentCalendarInteractor(
        storage=StudentDB(), presenter=StudentCalendarPresenter(),
    ).get_events(
        user=request.user,
        event_type=request.query_params.get('event_type'),
        start_date=request.query_params.get('start_date'),
        end_date=request.query_params.get('end_date'),
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsStudent | IsAdmin])
def exams_view(request):
    return StudentExamNotImplementedInteractor(presenter=StudentExamPresenter()).respond(user=request.user)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsStudent | IsAdmin])
def results_view(request):
    return StudentExamNotImplementedInteractor(presenter=StudentExamPresenter()).respond(user=request.user)
