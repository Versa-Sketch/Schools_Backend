from .base import _ensure_teacher


class TeacherStudentAttendanceInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def get_attendance(self, user, student_id, date_from=None, date_to=None, slot=None, status=None):
        _ensure_teacher(user)
        teacher_profile = self.storage.get_teacher_profile(user)
        records = self.storage.get_student_attendance(
            teacher_profile, student_id, date_from, date_to, slot, status,
        )
        return self.presenter.attendance_success(records=records)
