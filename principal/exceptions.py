from core.exceptions import PermissionDeniedException
from . import constants


class PrincipalPermissionException(PermissionDeniedException):
    def __init__(self, details=constants.PRINCIPAL_ROLE_REQUIRED):
        super().__init__(details=details, code=constants.ROLE_NOT_ALLOWED)
