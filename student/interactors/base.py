from student.exceptions import StudentPermissionException


def _ensure_student(user):
    if user.role != 'STUDENT':
        raise StudentPermissionException()
