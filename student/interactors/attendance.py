from core.exceptions import NotFoundException
from .base import _ensure_student


class StudentAttendanceInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def get_attendance(self, user, date_from=None, date_to=None, slot=None, status=None):
        _ensure_student(user)
        profile = self.storage.get_student_profile(user)
        if profile is None:
            raise NotFoundException('Student profile not found.')
        records = self.storage.get_attendance(profile, date_from, date_to, slot, status)
        return self.presenter.attendance_success(records=records)
