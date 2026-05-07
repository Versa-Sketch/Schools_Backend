from student.exceptions import StudentPermissionException


def _ensure_student(user):
    if user.role not in ('ADMIN', 'STUDENT'):
        raise StudentPermissionException()
