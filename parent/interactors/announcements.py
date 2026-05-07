from core.exceptions import NotFoundException
from .base import _ensure_parent, _get_linked_student


class ParentStudentAnnouncementsInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def get_announcements(self, user, student_id, audience=None, published_after=None):
        _ensure_parent(user)
        profile = self.storage.get_parent_profile(user)
        if profile is None:
            raise NotFoundException('Parent profile not found.')
        student = _get_linked_student(self.storage, profile, student_id)
        announcements = self.storage.get_announcements_for_student(student, audience, published_after)
        return self.presenter.announcement_list_success(announcements=announcements)
