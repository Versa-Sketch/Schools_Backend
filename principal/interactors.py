from .exceptions import PrincipalPermissionException


class PrincipalBaseInteractor:
    def ensure_principal(self, user):
        if user.role != 'PRINCIPAL':
            raise PrincipalPermissionException()
