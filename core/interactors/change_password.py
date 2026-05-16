from core import constants
from core.exceptions import AuthenticationFailedException, ValidationException


class ChangePasswordInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def change_password(self, user, current_password, new_password, confirm_password):
        if not current_password:
            raise ValidationException(constants.CURRENT_PASSWORD_REQUIRED)
        if not new_password:
            raise ValidationException(constants.NEW_PASSWORD_REQUIRED)
        if not confirm_password:
            raise ValidationException(constants.CONFIRM_PASSWORD_REQUIRED)
        if new_password != confirm_password:
            raise ValidationException(constants.PASSWORDS_DO_NOT_MATCH)
        if not user.check_password(current_password):
            raise AuthenticationFailedException(constants.INCORRECT_CURRENT_PASSWORD)
        self.storage.update_password(user, new_password)
        return self.presenter.success()
