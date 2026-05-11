from .base import _ensure_principal


class DailyAttendanceSummaryInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def get_summary(self, user, date):
        _ensure_principal(user)
        profile = self.storage.get_principal_profile(user)
        rows = self.storage.get_daily_class_attendance_summary(profile.school_id, date)
        return self.presenter.summary_success(date, rows)


class ClassAttendanceDetailInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def get_detail(self, user, class_id, date):
        _ensure_principal(user)
        profile = self.storage.get_principal_profile(user)
        academic_class = self.storage.get_academic_class_by_id(profile.school_id, class_id)
        sections = self.storage.get_class_attendance_detail(profile.school_id, class_id, date)
        return self.presenter.detail_success(date, academic_class, sections)
