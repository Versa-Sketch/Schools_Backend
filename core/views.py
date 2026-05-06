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

from .jwt_auth.jwt_tokens import UserAuthentication

from .presenters.current_user import CurrentUserPresenter
from .presenters.login import LoginPresenter
from .presenters.logout import LogoutPresenter
from .presenters.refresh_token import RefreshTokenPresenter

from .storages.user_storage import UserDB




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
