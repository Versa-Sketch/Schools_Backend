from core.exceptions import NotFoundException
from .base import _ensure_parent, _get_linked_student


class ParentStudentHomeworkInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def get_homework(self, user, student_id, subject_id=None, deadline_from=None, deadline_to=None):
        _ensure_parent(user)
        profile = self.storage.get_parent_profile(user)
        if profile is None:
            raise NotFoundException('Parent profile not found.')
        student = _get_linked_student(self.storage, profile, student_id)
        homework = self.storage.get_homework_for_student(student, subject_id, deadline_from, deadline_to)
        return self.presenter.homework_list_success(homework=homework)
