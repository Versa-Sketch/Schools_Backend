from core.exceptions import NotFoundException, ValidationException
from analytics.constants import ANALYTICS_STATUS_DONE
from analytics.exceptions import AnalyticsValidationError, ExamNotFoundError
from principal.exceptions import PrincipalPermissionException


class DashboardInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def list_exams(self, user):
        self._check_role(user)
        profile = self._get_profile(user)
        exams = self.storage.get_exams_for_school(profile.school_id)
        return self.presenter.exams_only(exams)

    def get_dashboard(self, user, exam_id):
        self._check_role(user)
        profile = self._get_profile(user)
        school_id = profile.school_id

        exams = self.storage.get_exams_for_school(school_id)

        if not exam_id:
            return self.presenter.exams_only(exams)

        exam = self.storage.get_exam_by_id(exam_id, school_id)
        if exam is None:
            raise ExamNotFoundError()

        if exam.analytics_status != ANALYTICS_STATUS_DONE:
            return self.presenter.exam_not_ready(exam, exams)

        section_analytics = self.storage.get_section_analytics_for_exam(exam_id)
        subject_stats     = self.storage.get_subject_overall_stats(exam_id, school_id)

        return self.presenter.dashboard_success(
            exam=exam,
            exams=exams,
            section_analytics=section_analytics,
            subject_stats=subject_stats,
        )

    def get_class_detail(self, user, class_name, exam_id):
        self._check_role(user)
        profile = self._get_profile(user)
        school_id = profile.school_id

        if not exam_id:
            raise ValidationException('exam_id query parameter is required.')

        exam = self.storage.get_exam_by_id(exam_id, school_id)
        if exam is None:
            raise ExamNotFoundError()

        if exam.analytics_status != ANALYTICS_STATUS_DONE:
            raise AnalyticsValidationError(
                f'Analytics is not ready yet (status: {exam.analytics_status}).'
            )

        section_analytics = self.storage.get_section_analytics_for_class(
            exam_id, class_name, school_id
        )
        student_counts = self.storage.get_student_counts_for_exam(exam_id, school_id)

        return self.presenter.class_detail_success(
            class_name=class_name,
            exam=exam,
            section_analytics=section_analytics,
            student_counts=student_counts,
        )

    # ---------------------------------------------------------------- helpers

    def _check_role(self, user):
        if user.role not in ('ADMIN', 'PRINCIPAL'):
            raise PrincipalPermissionException()

    def _get_profile(self, user):
        profile = self.storage.get_principal_profile(user)
        if profile is None:
            raise NotFoundException('Principal profile not found.')
        return profile
