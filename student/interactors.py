from .exceptions import StudentPermissionException


class StudentBaseInteractor:
    def ensure_student(self, user):
        if user.role != 'STUDENT':
            raise StudentPermissionException()
