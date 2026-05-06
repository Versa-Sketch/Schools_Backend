from rest_framework_simplejwt.exceptions import TokenError

from . import constants
from .exceptions import (
    AuthenticationFailedException,
    PermissionDeniedException,
)


class LoginInteractor:
    def __init__(self, storage, presenter, authentication):
        self.storage = storage
        self.presenter = presenter
        self.authentication = authentication

    def login_interactor(self, phone_number, password):
        user = self.storage.get_user_by_phone_number(phone_number=phone_number)
        if user is None or not user.check_password(password):
            raise AuthenticationFailedException(constants.INVALID_CREDENTIALS)
        if not user.is_active:
            raise PermissionDeniedException(constants.INACTIVE_USER)

        profile = self.storage.get_user_profile(user)
        tokens = self.authentication.create_tokens(user)
        return self.presenter.success(tokens=tokens, user=user, profile=profile)


class RefreshTokenInteractor:
    def __init__(self, presenter, authentication):
        self.presenter = presenter
        self.authentication = authentication

    def refresh_interactor(self, refresh):
        try:
            tokens = self.authentication.refresh_access_token(refresh)
        except TokenError:
            raise AuthenticationFailedException(constants.INVALID_REFRESH_TOKEN)
        return self.presenter.success(tokens=tokens)


class LogoutInteractor:
    def __init__(self, presenter, authentication):
        self.presenter = presenter
        self.authentication = authentication

    def logout_interactor(self, refresh):
        try:
            self.authentication.blacklist_refresh_token(refresh)
        except TokenError:
            raise AuthenticationFailedException(constants.INVALID_REFRESH_TOKEN)
        return self.presenter.success()


class CurrentUserInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def get_current_user(self, user):
        profile = self.storage.get_user_profile(user)
        return self.presenter.success(user=user, profile=profile)
