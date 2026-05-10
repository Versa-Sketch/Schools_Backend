from core import constants
from core.exceptions import (
    PermissionDeniedException,
    ValidationException,
)


class LoginInteractor:
    def __init__(self, storage, presenter, authentication):
        self.storage = storage
        self.presenter = presenter
        self.authentication = authentication

    def login_interactor(self, phone_number, password):
        if not phone_number:
            raise ValidationException(constants.PHONE_NUMBER_REQUIRED)
        if not password:
            raise ValidationException(constants.PASSWORD_REQUIRED)
        
        user = self.storage.get_user_by_phone_number(phone_number=phone_number)
        if user is None or not user.check_password(password):
            raise ValidationException(constants.INVALID_CREDENTIALS)
        if not user.is_active:
            raise PermissionDeniedException(constants.INACTIVE_USER)

        profile = self.storage.get_user_profile(user)
        tokens = self.authentication.create_tokens(user)
        return self.presenter.success(tokens=tokens, user=user, profile=profile)
