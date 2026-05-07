from principal.exceptions import PrincipalPermissionException


def _ensure_principal(user):
    if user.role not in ('ADMIN', 'PRINCIPAL'):
        raise PrincipalPermissionException()
