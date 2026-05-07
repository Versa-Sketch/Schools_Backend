from core.exceptions import NotFoundException
from .base import _ensure_student


class StudentAnnouncementsInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def get_announcements(self, user, audience=None, published_after=None):
        _ensure_student(user)
        profile = self.storage.get_student_profile(user)
        if profile is None:
            raise NotFoundException('Student profile not found.')
        announcements = self.storage.get_announcements_for_student(profile, audience, published_after)
        return self.presenter.announcement_list_success(announcements=announcements)
