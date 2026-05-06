from rest_framework_simplejwt.exceptions import TokenError
from core import constants
from core.exceptions import AuthenticationFailedException, ValidationException

class LogoutInteractor:
    def __init__(self, presenter, authentication):
        self.presenter = presenter
        self.authentication = authentication

    def logout_interactor(self, refresh):
        if not refresh:
            raise ValidationException(constants.REFRESH_TOKEN_REQUIRED)
            
        try:
            self.authentication.blacklist_refresh_token(refresh)
        except TokenError:
            raise AuthenticationFailedException(constants.INVALID_REFRESH_TOKEN)
        return self.presenter.success()
