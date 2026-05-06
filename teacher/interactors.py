from .exceptions import TeacherPermissionException


class TeacherBaseInteractor:
    def ensure_teacher(self, user):
        if user.role != 'TEACHER':
            raise TeacherPermissionException()
