from core.exceptions import PermissionDeniedException
from parent.exceptions import ParentPermissionException
from parent import constants


def _ensure_parent(user):
    if user.role != 'PARENT':
        raise ParentPermissionException()


def _get_linked_student(storage, parent_profile, student_id):
    student = storage.get_linked_student_by_id(parent_profile, student_id)
    if student is None:
        raise PermissionDeniedException(constants.STUDENT_NOT_LINKED)
    return student
