from rest_framework_simplejwt.exceptions import TokenError
from core import constants
from core.exceptions import AuthenticationFailedException, ValidationException

class RefreshTokenInteractor:
    def __init__(self, presenter, authentication):
        self.presenter = presenter
        self.authentication = authentication

    def refresh_interactor(self, refresh):
        if not refresh:
            raise ValidationException(constants.REFRESH_TOKEN_REQUIRED)
            
        try:
            tokens = self.authentication.refresh_access_token(refresh)
        except TokenError:
            raise AuthenticationFailedException(constants.INVALID_REFRESH_TOKEN)
        return self.presenter.success(tokens=tokens)
