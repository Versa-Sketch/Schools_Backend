from .exceptions import ParentPermissionException


class ParentBaseInteractor:
    def ensure_parent(self, user):
        if user.role != 'PARENT':
            raise ParentPermissionException()
