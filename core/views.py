from rest_framework.decorators import api_view, authentication_classes, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import JSONParser
from rest_framework.response import Response

from . import constants
from .exceptions import AppException, ValidationException
from .interactors import (
    CurrentUserInteractor,
    LoginInteractor,
    LogoutInteractor,
    RefreshTokenInteractor,
)
from .jwt_auth.jwt_tokens import UserAuthentication
from .presenters import (
    CommonErrorPresenter,
    CurrentUserPresenter,
    LoginPresenter,
    LogoutPresenter,
    RefreshTokenPresenter,
)
from .storage import UserDB


def build_response(interactor_response):
    payload, status_code = interactor_response
    return Response(payload, status=status_code)


def build_error_response(exception):
    payload, status_code = CommonErrorPresenter().error(exception)
    return Response(payload, status=status_code)


def required_value(request, field_name, message):
    value = request.data.get(field_name)
    if value in (None, ''):
        raise ValidationException(message)
    return value


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
@parser_classes([JSONParser])
def login_view(request):
    try:
        phone_number = required_value(request, 'phone_number', constants.PHONE_NUMBER_REQUIRED)
        password = required_value(request, 'password', constants.PASSWORD_REQUIRED)
        response = LoginInteractor(
            storage=UserDB(),
            presenter=LoginPresenter(),
            authentication=UserAuthentication(),
        ).login_interactor(phone_number=phone_number, password=password)
        return build_response(response)
    except AppException as exception:
        return build_error_response(exception)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
@parser_classes([JSONParser])
def refresh_token_view(request):
    try:
        refresh = required_value(request, 'refresh', constants.REFRESH_TOKEN_REQUIRED)
        response = RefreshTokenInteractor(
            presenter=RefreshTokenPresenter(),
            authentication=UserAuthentication(),
        ).refresh_interactor(refresh=refresh)
        return build_response(response)
    except AppException as exception:
        return build_error_response(exception)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([JSONParser])
def logout_view(request):
    try:
        refresh = required_value(request, 'refresh', constants.REFRESH_TOKEN_REQUIRED)
        response = LogoutInteractor(
            presenter=LogoutPresenter(),
            authentication=UserAuthentication(),
        ).logout_interactor(refresh=refresh)
        return build_response(response)
    except AppException as exception:
        return build_error_response(exception)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user_view(request):
    response = CurrentUserInteractor(
        storage=UserDB(),
        presenter=CurrentUserPresenter(),
    ).get_current_user(user=request.user)
    return build_response(response)
