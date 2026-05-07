from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser

from core.permissions import IsTeacher
from .storages.teacher_storage import TeacherDB
from .interactors import (
    ListSectionsInteractor,
    ListSectionStudentsInteractor,
    CreateAttendanceSessionInteractor,
    MarkAttendanceInteractor,
    ConfirmAttendanceInteractor,
    CreateTeacherAnnouncementInteractor,
    CreateStudyMaterialInteractor,
    ListStudyMaterialsInteractor,
    CreateHomeworkInteractor,
    ListHomeworkInteractor,
    ListParentQueriesInteractor,
    ReplyToQueryInteractor,
    ExamMarksNotImplementedInteractor,
    UpdateTeacherProfilePicInteractor,
)
from .presenters.sections import SectionsPresenter
from .presenters.attendance import AttendancePresenter
from .presenters.announcements import AnnouncementPresenter
from .presenters.study_materials import StudyMaterialsPresenter
from .presenters.homework import HomeworkPresenter
from .presenters.parent_queries import ParentQueriesPresenter
from .presenters.exams import ExamPresenter
from .presenters.profile_pic import ProfilePicPresenter


@api_view(['PATCH'])
@permission_classes([IsAuthenticated, IsTeacher])
@parser_classes([MultiPartParser, FormParser])
def profile_pic_view(request):
    return UpdateTeacherProfilePicInteractor(
        presenter=ProfilePicPresenter(),
    ).update(user=request.user, file=request.FILES.get('profile_pic'))


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsTeacher])
def sections_view(request):
    return ListSectionsInteractor(
        storage=TeacherDB(), presenter=SectionsPresenter(),
    ).list_sections(user=request.user)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsTeacher])
def section_students_view(request, section_id):
    return ListSectionStudentsInteractor(
        storage=TeacherDB(), presenter=SectionsPresenter(),
    ).list_students(user=request.user, section_id=section_id)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsTeacher])
@parser_classes([JSONParser])
def attendance_session_create_view(request):
    return CreateAttendanceSessionInteractor(
        storage=TeacherDB(), presenter=AttendancePresenter(),
    ).create_session(user=request.user, data=request.data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated, IsTeacher])
@parser_classes([JSONParser])
def attendance_students_view(request, session_id):
    return MarkAttendanceInteractor(
        storage=TeacherDB(), presenter=AttendancePresenter(),
    ).mark_attendance(user=request.user, session_id=session_id, data=request.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsTeacher])
def attendance_confirm_view(request, session_id):
    return ConfirmAttendanceInteractor(
        storage=TeacherDB(), presenter=AttendancePresenter(),
    ).confirm_session(user=request.user, session_id=session_id)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsTeacher])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def announcement_create_view(request):
    return CreateTeacherAnnouncementInteractor(
        storage=TeacherDB(), presenter=AnnouncementPresenter(),
    ).create_announcement(user=request.user, data=request.data, files=request.FILES.getlist('attachments'))


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, IsTeacher])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def study_material_view(request):
    if request.method == 'POST':
        return CreateStudyMaterialInteractor(
            storage=TeacherDB(), presenter=StudyMaterialsPresenter(),
        ).create_material(user=request.user, data=request.data, file=request.FILES.get('file'))
    return ListStudyMaterialsInteractor(
        storage=TeacherDB(), presenter=StudyMaterialsPresenter(),
    ).list_materials(
        user=request.user,
        section_id=request.query_params.get('section_id'),
        subject_id=request.query_params.get('subject_id'),
        date_from=request.query_params.get('date_from'),
        date_to=request.query_params.get('date_to'),
    )


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, IsTeacher])
@parser_classes([JSONParser])
def homework_view(request):
    if request.method == 'POST':
        return CreateHomeworkInteractor(
            storage=TeacherDB(), presenter=HomeworkPresenter(),
        ).create_homework(user=request.user, data=request.data)
    return ListHomeworkInteractor(
        storage=TeacherDB(), presenter=HomeworkPresenter(),
    ).list_homework(
        user=request.user,
        section_id=request.query_params.get('section_id'),
        subject_id=request.query_params.get('subject_id'),
        deadline_from=request.query_params.get('deadline_from'),
        deadline_to=request.query_params.get('deadline_to'),
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsTeacher])
def parent_query_list_view(request):
    return ListParentQueriesInteractor(
        storage=TeacherDB(), presenter=ParentQueriesPresenter(),
    ).list_queries(
        user=request.user,
        status=request.query_params.get('status'),
        section_id=request.query_params.get('section_id'),
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsTeacher])
@parser_classes([JSONParser])
def parent_query_reply_view(request, query_id):
    return ReplyToQueryInteractor(
        storage=TeacherDB(), presenter=ParentQueriesPresenter(),
    ).reply(user=request.user, query_id=query_id, data=request.data)


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated, IsTeacher])
def exam_marks_view(request, exam_id):
    return ExamMarksNotImplementedInteractor(presenter=ExamPresenter()).respond(user=request.user)
