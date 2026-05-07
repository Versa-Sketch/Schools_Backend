from principal.exceptions import PrincipalPermissionException


def _ensure_principal(user):
    if user.role != 'PRINCIPAL':
        raise PrincipalPermissionException()
