from rest_framework import status

from . import constants


class AppException(Exception):
    code = constants.VALIDATION_ERROR
    details = 'Invalid request.'
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, details=None, code=None, status_code=None):
        self.details = details or self.details
        self.code = code or self.code
        self.status_code = status_code or self.status_code
        super().__init__(self.details)


class ValidationException(AppException):
    code = constants.VALIDATION_ERROR
    status_code = status.HTTP_400_BAD_REQUEST


class AuthenticationFailedException(AppException):
    code = constants.AUTHENTICATION_FAILED
    status_code = status.HTTP_401_UNAUTHORIZED


class PermissionDeniedException(AppException):
    code = constants.PERMISSION_DENIED
    status_code = status.HTTP_403_FORBIDDEN


class NotFoundException(AppException):
    code = constants.NOT_FOUND
    status_code = status.HTTP_404_NOT_FOUND


class SchoolScopeException(AppException):
    code = constants.SCHOOL_SCOPE_ERROR
    status_code = status.HTTP_403_FORBIDDEN
