from rest_framework.decorators import api_view, authentication_classes, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import JSONParser
from rest_framework.response import Response

from . import constants
from .exceptions import AppException, ValidationException
from .interactors.current_user import CurrentUserInteractor
from .interactors.login import LoginInteractor
from .interactors.logout import LogoutInteractor
from .interactors.refresh_token import RefreshTokenInteractor
from .interactors.school import SchoolInteractor
from .interactors.lookup import (
    ClassListInteractor,
    SectionListInteractor,
    SectionStudentsInteractor,
    StudentDetailInteractor,
    SubjectListInteractor,
)
from .interactors.calendar_events import CalendarEventListInteractor
from .interactors.announcements import AnnouncementListInteractor, AnnouncementDetailInteractor
from .interactors.change_password import ChangePasswordInteractor

from .jwt_auth.jwt_tokens import UserAuthentication

from .presenters.current_user import CurrentUserPresenter
from .presenters.login import LoginPresenter
from .presenters.logout import LogoutPresenter
from .presenters.refresh_token import RefreshTokenPresenter
from .presenters.school import SchoolPresenter
from .presenters.lookup import LookupPresenter
from .presenters.calendar_events import CalendarEventPresenter
from .presenters.announcements import AnnouncementPresenter
from .presenters.change_password import ChangePasswordPresenter

from .storages.user_storage import UserDB
from .storages.core_storage import CoreDB


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
@parser_classes([JSONParser])
def login_view(request):
    phone_number = request.data.get('phone_number')
    password = request.data.get('password')
    return LoginInteractor(
        storage=UserDB(),
        presenter=LoginPresenter(),
        authentication=UserAuthentication(),
    ).login_interactor(phone_number=phone_number, password=password)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
@parser_classes([JSONParser])
def refresh_token_view(request):
    refresh = request.data.get('refresh')
    return RefreshTokenInteractor(
        presenter=RefreshTokenPresenter(),
        authentication=UserAuthentication(),
    ).refresh_interactor(refresh=refresh)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([JSONParser])
def logout_view(request):
    refresh = request.data.get('refresh')
    return LogoutInteractor(
        presenter=LogoutPresenter(),
        authentication=UserAuthentication(),
    ).logout_interactor(refresh=refresh)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user_view(request):
    return CurrentUserInteractor(
        storage=UserDB(),
        presenter=CurrentUserPresenter(),
    ).get_current_user(user=request.user)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def school_view(request):
    return SchoolInteractor(
        storage=CoreDB(),
        presenter=SchoolPresenter(),
    ).get_school(user=request.user)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def class_list_view(request):
    return ClassListInteractor(
        storage=CoreDB(),
        presenter=LookupPresenter(),
    ).get_classes(user=request.user)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def section_list_view(request):
    class_id = request.query_params.get('class_id')
    return SectionListInteractor(
        storage=CoreDB(),
        presenter=LookupPresenter(),
    ).get_sections(user=request.user, class_id=class_id)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def section_students_view(request, section_id):
    return SectionStudentsInteractor(
        storage=CoreDB(),
        presenter=LookupPresenter(),
    ).get_students(user=request.user, section_id=section_id)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_detail_view(request, student_id):
    return StudentDetailInteractor(
        storage=CoreDB(),
        presenter=LookupPresenter(),
    ).get_student(user=request.user, student_id=student_id, date=request.query_params.get('date'))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def subject_list_view(request):
    return SubjectListInteractor(
        storage=CoreDB(),
        presenter=LookupPresenter(),
    ).get_subjects(user=request.user)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def calendar_event_list_view(request):
    event_type = request.query_params.get('event_type')
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    month = request.query_params.get('month')
    year = request.query_params.get('year')
    return CalendarEventListInteractor(
        storage=CoreDB(),
        presenter=CalendarEventPresenter(),
    ).get_calendar_events(
        user=request.user,
        event_type=event_type,
        start_date=start_date,
        end_date=end_date,
        month=month,
        year=year,
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def announcement_list_view(request):
    audience = request.query_params.get('audience')
    published_after = request.query_params.get('published_after')
    return AnnouncementListInteractor(
        storage=CoreDB(),
        presenter=AnnouncementPresenter(),
    ).get_announcements(user=request.user, audience=audience, published_after=published_after)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([JSONParser])
def change_password_view(request):
    return ChangePasswordInteractor(
        storage=UserDB(),
        presenter=ChangePasswordPresenter(),
    ).change_password(
        user=request.user,
        current_password=request.data.get('current_password'),
        new_password=request.data.get('new_password'),
        confirm_password=request.data.get('confirm_password'),
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def announcement_detail_view(request, announcement_id):
    return AnnouncementDetailInteractor(
        storage=CoreDB(),
        presenter=AnnouncementPresenter(),
    ).get_announcement(user=request.user, announcement_id=announcement_id)
