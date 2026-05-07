from core.exceptions import NotFoundException
from .base import _ensure_student


class StudentCalendarInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def get_events(self, user, event_type=None, start_date=None, end_date=None):
        _ensure_student(user)
        profile = self.storage.get_student_profile(user)
        if profile is None:
            raise NotFoundException('Student profile not found.')
        events = self.storage.get_calendar_events_for_student(profile, event_type, start_date, end_date)
        return self.presenter.calendar_list_success(events=events)
