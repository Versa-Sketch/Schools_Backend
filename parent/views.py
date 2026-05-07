from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser

from core.permissions import IsAdmin, IsParent
from .storages.parent_storage import ParentDB
from .interactors import (
    ParentProfileInteractor,
    ListLinkedStudentsInteractor,
    ParentStudentAttendanceInteractor,
    ParentStudentAnnouncementsInteractor,
    ParentStudentMaterialsInteractor,
    ParentStudentHomeworkInteractor,
    ParentStudentCalendarInteractor,
    ParentStudentResultsInteractor,
    CreateParentQueryInteractor,
    ListParentQueriesInteractor,
    GetParentQueryDetailInteractor,
    AddParentQueryReplyInteractor,
    UpdateParentProfilePicInteractor,
)
from .presenters.profile import ParentProfilePresenter
from .presenters.attendance import ParentAttendancePresenter
from .presenters.announcements import ParentAnnouncementsPresenter
from .presenters.study_materials import ParentStudyMaterialsPresenter
from .presenters.homework import ParentHomeworkPresenter
from .presenters.calendar import ParentCalendarPresenter
from .presenters.exams import ParentExamPresenter
from .presenters.queries import ParentQueriesPresenter
from .presenters.profile_pic import ProfilePicPresenter


@api_view(['PATCH'])
@permission_classes([IsAuthenticated, IsParent | IsAdmin])
@parser_classes([MultiPartParser, FormParser])
def profile_pic_view(request):
    return UpdateParentProfilePicInteractor(
        presenter=ProfilePicPresenter(),
    ).update(user=request.user, file=request.FILES.get('profile_pic'))


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsParent | IsAdmin])
def profile_view(request):
    return ParentProfileInteractor(
        storage=ParentDB(), presenter=ParentProfilePresenter(),
    ).get_profile(user=request.user)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsParent | IsAdmin])
def students_view(request):
    return ListLinkedStudentsInteractor(
        storage=ParentDB(), presenter=ParentProfilePresenter(),
    ).list_students(user=request.user)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsParent | IsAdmin])
def student_attendance_view(request, student_id):
    return ParentStudentAttendanceInteractor(
        storage=ParentDB(), presenter=ParentAttendancePresenter(),
    ).get_attendance(
        user=request.user, student_id=student_id,
        date_from=request.query_params.get('date_from'),
        date_to=request.query_params.get('date_to'),
        slot=request.query_params.get('slot'),
        status=request.query_params.get('status'),
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsParent | IsAdmin])
def student_announcements_view(request, student_id):
    return ParentStudentAnnouncementsInteractor(
        storage=ParentDB(), presenter=ParentAnnouncementsPresenter(),
    ).get_announcements(
        user=request.user, student_id=student_id,
        audience=request.query_params.get('audience'),
        published_after=request.query_params.get('published_after'),
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsParent | IsAdmin])
def student_study_materials_view(request, student_id):
    return ParentStudentMaterialsInteractor(
        storage=ParentDB(), presenter=ParentStudyMaterialsPresenter(),
    ).get_materials(
        user=request.user, student_id=student_id,
        subject_id=request.query_params.get('subject_id'),
        date_from=request.query_params.get('date_from'),
        date_to=request.query_params.get('date_to'),
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsParent | IsAdmin])
def student_homework_view(request, student_id):
    return ParentStudentHomeworkInteractor(
        storage=ParentDB(), presenter=ParentHomeworkPresenter(),
    ).get_homework(
        user=request.user, student_id=student_id,
        subject_id=request.query_params.get('subject_id'),
        deadline_from=request.query_params.get('deadline_from'),
        deadline_to=request.query_params.get('deadline_to'),
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsParent | IsAdmin])
def student_calendar_view(request, student_id):
    return ParentStudentCalendarInteractor(
        storage=ParentDB(), presenter=ParentCalendarPresenter(),
    ).get_events(
        user=request.user, student_id=student_id,
        event_type=request.query_params.get('event_type'),
        start_date=request.query_params.get('start_date'),
        end_date=request.query_params.get('end_date'),
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsParent | IsAdmin])
def student_results_view(request, student_id):
    return ParentStudentResultsInteractor(presenter=ParentExamPresenter()).respond(user=request.user)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, IsParent | IsAdmin])
@parser_classes([JSONParser])
def query_list_view(request):
    if request.method == 'POST':
        return CreateParentQueryInteractor(
            storage=ParentDB(), presenter=ParentQueriesPresenter(),
        ).create_query(user=request.user, data=request.data)
    return ListParentQueriesInteractor(
        storage=ParentDB(), presenter=ParentQueriesPresenter(),
    ).list_queries(
        user=request.user,
        student_id=request.query_params.get('student_id'),
        status=request.query_params.get('status'),
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsParent | IsAdmin])
def query_detail_view(request, query_id):
    return GetParentQueryDetailInteractor(
        storage=ParentDB(), presenter=ParentQueriesPresenter(),
    ).get_query(user=request.user, query_id=query_id)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsParent | IsAdmin])
@parser_classes([JSONParser])
def query_reply_view(request, query_id):
    return AddParentQueryReplyInteractor(
        storage=ParentDB(), presenter=ParentQueriesPresenter(),
    ).add_reply(user=request.user, query_id=query_id, data=request.data)
