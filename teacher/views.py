from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser

from core.permissions import IsAdmin, IsTeacher
from .storages.teacher_storage import TeacherDB
from django.utils.dateparse import parse_date

from .interactors import (
    ListSectionsInteractor,
    ListSectionStudentsInteractor,
    CreateAttendanceSessionInteractor,
    MarkAttendanceInteractor,
    ConfirmAttendanceInteractor,
    CreateTeacherAnnouncementInteractor,
    UpdateTeacherAnnouncementInteractor,
    DeleteTeacherAnnouncementInteractor,
    CreateStudyMaterialInteractor,
    ListStudyMaterialsInteractor,
    CreateHomeworkInteractor,
    ListHomeworkInteractor,
    ListParentQueriesInteractor,
    ReplyToQueryInteractor,
    CloseQueryInteractor,
    GetQueryDetailInteractor,
    ExamMarksNotImplementedInteractor,
    UpdateTeacherProfilePicInteractor,
    TeacherStudentAttendanceInteractor,
)
from .presenters.sections import SectionsPresenter
from .presenters.attendance import AttendancePresenter
from .presenters.announcements import AnnouncementPresenter
from .presenters.study_materials import StudyMaterialsPresenter
from .presenters.homework import HomeworkPresenter
from .presenters.parent_queries import ParentQueriesPresenter
from .presenters.exams import ExamPresenter
from .presenters.profile_pic import ProfilePicPresenter
from student.presenters.attendance import StudentAttendancePresenter


@api_view(['PATCH'])
@permission_classes([IsAuthenticated, IsTeacher | IsAdmin])
@parser_classes([MultiPartParser, FormParser])
def profile_pic_view(request):
    return UpdateTeacherProfilePicInteractor(
        presenter=ProfilePicPresenter(),
    ).update(user=request.user, file=request.FILES.get('profile_pic'))


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsTeacher | IsAdmin])
def sections_view(request):
    return ListSectionsInteractor(
        storage=TeacherDB(), presenter=SectionsPresenter(),
    ).list_sections(user=request.user)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsTeacher | IsAdmin])
def section_students_view(request, section_id):
    return ListSectionStudentsInteractor(
        storage=TeacherDB(), presenter=SectionsPresenter(),
    ).list_students(user=request.user, section_id=section_id)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsTeacher | IsAdmin])
@parser_classes([JSONParser])
def attendance_session_create_view(request):
    return CreateAttendanceSessionInteractor(
        storage=TeacherDB(), presenter=AttendancePresenter(),
    ).create_session(user=request.user, data=request.data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated, IsTeacher | IsAdmin])
@parser_classes([JSONParser])
def attendance_students_view(request, session_id):
    return MarkAttendanceInteractor(
        storage=TeacherDB(), presenter=AttendancePresenter(),
    ).mark_attendance(user=request.user, session_id=session_id, data=request.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsTeacher | IsAdmin])
def attendance_confirm_view(request, session_id):
    return ConfirmAttendanceInteractor(
        storage=TeacherDB(), presenter=AttendancePresenter(),
    ).confirm_session(user=request.user, session_id=session_id)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsTeacher | IsAdmin])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def announcement_create_view(request):
    return CreateTeacherAnnouncementInteractor(
        storage=TeacherDB(), presenter=AnnouncementPresenter(),
    ).create_announcement(user=request.user, data=request.data, files=request.FILES.getlist('attachments'))


@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAuthenticated, IsTeacher | IsAdmin])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def announcement_detail_view(request, announcement_id):
    if request.method == 'DELETE':
        return DeleteTeacherAnnouncementInteractor(
            storage=TeacherDB(), presenter=AnnouncementPresenter(),
        ).delete_announcement(user=request.user, announcement_id=announcement_id)
    return UpdateTeacherAnnouncementInteractor(
        storage=TeacherDB(), presenter=AnnouncementPresenter(),
    ).update_announcement(
        user=request.user,
        announcement_id=announcement_id,
        data=request.data,
        files=request.FILES.getlist('attachments'),
    )


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, IsTeacher | IsAdmin])
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
@permission_classes([IsAuthenticated, IsTeacher | IsAdmin])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def homework_view(request):
    if request.method == 'POST':
        files = request.FILES.getlist('files') or request.FILES.getlist('attachments') or request.FILES.getlist('file')
        return CreateHomeworkInteractor(
            storage=TeacherDB(), presenter=HomeworkPresenter(),
        ).create_homework(
            user=request.user,
            data=request.data,
            files=files,
        )
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
@permission_classes([IsAuthenticated, IsTeacher | IsAdmin])
def parent_query_list_view(request):
    return ListParentQueriesInteractor(
        storage=TeacherDB(), presenter=ParentQueriesPresenter(),
    ).list_queries(
        user=request.user,
        status=request.query_params.get('status'),
        section_id=request.query_params.get('section_id'),
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsTeacher | IsAdmin])
def parent_query_detail_view(request, query_id):
    return GetQueryDetailInteractor(
        storage=TeacherDB(), presenter=ParentQueriesPresenter(),
    ).get_detail(user=request.user, query_id=query_id)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsTeacher | IsAdmin])
@parser_classes([JSONParser])
def parent_query_reply_view(request, query_id):
    return ReplyToQueryInteractor(
        storage=TeacherDB(), presenter=ParentQueriesPresenter(),
    ).reply(user=request.user, query_id=query_id, data=request.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsTeacher | IsAdmin])
def parent_query_close_view(request, query_id):
    return CloseQueryInteractor(
        storage=TeacherDB(), presenter=ParentQueriesPresenter(),
    ).close(user=request.user, query_id=query_id)


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated, IsTeacher | IsAdmin])
def exam_marks_view(request, exam_id):
    return ExamMarksNotImplementedInteractor(presenter=ExamPresenter()).respond(user=request.user)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsTeacher | IsAdmin])
def teacher_student_attendance_view(request, student_id):
    date_from = parse_date(request.query_params.get('date_from')) if request.query_params.get('date_from') else None
    date_to = parse_date(request.query_params.get('date_to')) if request.query_params.get('date_to') else None
    slot = request.query_params.get('slot')
    status = request.query_params.get('status')
    return TeacherStudentAttendanceInteractor(
        storage=TeacherDB(), presenter=StudentAttendancePresenter(),
    ).get_attendance(user=request.user, student_id=student_id, date_from=date_from, date_to=date_to, slot=slot, status=status)
