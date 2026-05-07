from core.exceptions import NotFoundException
from .base import _ensure_student


class StudentProfileInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def get_profile(self, user):
        _ensure_student(user)
        profile = self.storage.get_student_profile(user)
        if profile is None:
            raise NotFoundException('Student profile not found.')
        return self.presenter.profile_success(profile=profile)
