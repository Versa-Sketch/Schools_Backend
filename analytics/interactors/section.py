from core.exceptions import NotFoundException, PermissionDeniedException, ValidationException
from analytics.constants import ANALYTICS_STATUS_DONE
from analytics.exceptions import AnalyticsValidationError, ExamNotFoundError


class SectionInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def get_section_students(self, user, section_id, exam_id):
        school_id = self._get_school_id(user)
        section   = self._get_section(section_id, school_id)
        self._check_section_access(user, section)
        exam = self._get_done_exam(exam_id, school_id)

        exam_results = self.storage.get_exam_results_for_section(
            exam_id, section.academic_class.name, section.name, school_id,
        )
        risk_map = self.storage.get_student_risks_for_section(
            exam_id, section.academic_class.name, section.name, school_id,
        )
        return self.presenter.section_students_success(section, exam, exam_results, risk_map)

    def get_question_heatmap(self, user, section_id, subject_id, exam_id):
        school_id = self._get_school_id(user)
        section   = self._get_section(section_id, school_id)
        self._check_section_access(user, section)
        exam = self._get_done_exam(exam_id, school_id)
        exam_subject = self._get_exam_subject(subject_id, exam_id)

        questions = self.storage.get_question_analytics_for_subject(exam_id, subject_id)
        return self.presenter.heatmap_success(
            section, exam_subject.subject_name, exam, questions
        )

    def get_question_detail(self, user, section_id, subject_id, q_no, exam_id):
        school_id = self._get_school_id(user)
        section   = self._get_section(section_id, school_id)
        self._check_section_access(user, section)
        exam = self._get_done_exam(exam_id, school_id)
        exam_subject = self._get_exam_subject(subject_id, exam_id)

        qa = self.storage.get_question_detail(exam_id, subject_id, q_no)
        if qa is None:
            raise NotFoundException(f'Question {q_no} not found.')
        return self.presenter.question_detail_success(
            section, exam_subject.subject_name, q_no, exam, qa
        )

    # ---------------------------------------------------------------- helpers

    def _get_school_id(self, user):
        if user.role in ('ADMIN', 'PRINCIPAL'):
            profile = self.storage.get_principal_profile(user)
            if profile is None:
                raise NotFoundException('Principal profile not found.')
            return profile.school_id
        if user.role == 'TEACHER':
            teacher = getattr(user, 'teacherprofile', None)
            if teacher is None:
                raise NotFoundException('Teacher profile not found.')
            return teacher.school_id
        raise PermissionDeniedException('Access denied.')

    def _get_section(self, section_id, school_id):
        if not section_id:
            raise ValidationException('section_id is required.')
        section = self.storage.get_section_by_id(section_id, school_id)
        if section is None:
            raise NotFoundException('Section not found.')
        return section

    def _check_section_access(self, user, section):
        if user.role in ('ADMIN', 'PRINCIPAL'):
            return
        if user.role == 'TEACHER':
            teacher = getattr(user, 'teacherprofile', None)
            if teacher is None:
                raise NotFoundException('Teacher profile not found.')
            assigned_ids = list(teacher.assigned_sections.values_list('id', flat=True))
            if section.id not in assigned_ids:
                raise PermissionDeniedException('You can only access your assigned sections.')
            return
        raise PermissionDeniedException('Access denied.')

    def _get_done_exam(self, exam_id, school_id):
        if not exam_id:
            raise ValidationException('exam_id is required.')
        exam = self.storage.get_exam_by_id(exam_id, school_id)
        if exam is None:
            raise ExamNotFoundError()
        if exam.analytics_status != ANALYTICS_STATUS_DONE:
            raise AnalyticsValidationError(
                f'Analytics not ready (status: {exam.analytics_status}).'
            )
        return exam

    def _get_exam_subject(self, subject_id, exam_id):
        if not subject_id:
            raise ValidationException('subject_id is required.')
        exam_subject = self.storage.get_exam_subject_by_id(subject_id, exam_id)
        if exam_subject is None:
            raise NotFoundException('Subject not found for this exam.')
        return exam_subject
