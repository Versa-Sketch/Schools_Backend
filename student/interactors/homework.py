from core.exceptions import NotFoundException
from .base import _ensure_student


class StudentHomeworkInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def get_homework(self, user, subject_id=None, deadline_from=None, deadline_to=None):
        _ensure_student(user)
        profile = self.storage.get_student_profile(user)
        if profile is None:
            raise NotFoundException('Student profile not found.')
        homework = self.storage.get_homework_for_student(profile, subject_id, deadline_from, deadline_to)
        return self.presenter.homework_list_success(homework=homework)
