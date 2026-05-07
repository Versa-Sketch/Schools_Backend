from core.exceptions import NotFoundException
from .base import _ensure_parent, _get_linked_student


class ParentStudentCalendarInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def get_events(self, user, student_id, event_type=None, start_date=None, end_date=None):
        _ensure_parent(user)
        profile = self.storage.get_parent_profile(user)
        if profile is None:
            raise NotFoundException('Parent profile not found.')
        student = _get_linked_student(self.storage, profile, student_id)
        events = self.storage.get_calendar_events_for_student(student, event_type, start_date, end_date)
        return self.presenter.calendar_list_success(events=events)
