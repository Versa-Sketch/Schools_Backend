from core.exceptions import PermissionDeniedException
from . import constants


class StudentPermissionException(PermissionDeniedException):
    def __init__(self, details=constants.STUDENT_ROLE_REQUIRED):
        super().__init__(details=details, code=constants.ROLE_NOT_ALLOWED)
