from core.exceptions import NotFoundException
from .base import _ensure_parent, _get_linked_student


class ParentStudentAttendanceInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def get_attendance(self, user, student_id, date_from=None, date_to=None, slot=None, status=None):
        _ensure_parent(user)
        profile = self.storage.get_parent_profile(user)
        if profile is None:
            raise NotFoundException('Parent profile not found.')
        student = _get_linked_student(self.storage, profile, student_id)
        records = self.storage.get_attendance_for_student(student, date_from, date_to, slot, status)
        return self.presenter.attendance_success(records=records)
