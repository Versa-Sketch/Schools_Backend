from teacher.exceptions import TeacherPermissionException


def _ensure_teacher(user):
    if user.role != 'TEACHER':
        raise TeacherPermissionException()
