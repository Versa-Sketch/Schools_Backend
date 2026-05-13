from core.exceptions import NotFoundException, PermissionDeniedException, ValidationException
from analytics.constants import ANALYTICS_STATUS_DONE
from analytics.exceptions import AnalyticsValidationError, ExamNotFoundError, StudentNotFoundError


class StudentInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    # ---------------------------------------------------------------- Screen 6

    def get_student_summary(self, user, student_id, exam_id):
        school_id = self._get_school_id(user)
        student = self._get_student(student_id, school_id)
        self._check_student_access(user, student, school_id)
        exam, exams = self._get_done_exam_with_list(exam_id, school_id)

        exam_results = self.storage.get_exam_results_for_student(exam_id, student_id, school_id)
        risk_map = self.storage.get_student_risks_by_student_id(exam_id, student_id, school_id)

        return self.presenter.student_summary_success(
            student=student,
            exam=exam,
            exams=exams,
            exam_results=exam_results,
            risk_map=risk_map,
        )

    # ---------------------------------------------------------------- Screen 7

    def get_student_subject(self, user, student_id, subject_id, exam_id):
        school_id = self._get_school_id(user)
        student = self._get_student(student_id, school_id)
        self._check_student_access(user, student, school_id)
        exam, _ = self._get_done_exam_with_list(exam_id, school_id)

        exam_subject = self.storage.get_exam_subject_by_id(subject_id, exam_id)
        if exam_subject is None:
            raise NotFoundException('Subject not found for this exam.')

        exam_result = self.storage.get_exam_result_for_student_subject(
            exam_id, student_id, subject_id, school_id
        )
        if exam_result is None:
            raise NotFoundException(
                f'No result found for subject {exam_subject.subject_name!r}.'
            )

        risk = self.storage.get_risk_for_student_subject(
            exam_id, student_id, subject_id, school_id
        )
        question_results = self.storage.get_question_results_by_student_id(
            exam_id, student_id, subject_id
        )

        return self.presenter.student_subject_success(
            student=student,
            exam=exam,
            subject_name=exam_subject.subject_name,
            exam_result=exam_result,
            risk=risk,
            question_results=question_results,
        )

    # ---------------------------------------------------------------- All Exams

    def get_student_all_exams(self, user, student_id):
        school_id = self._get_school_id(user)
        student = self._get_student(student_id, school_id)
        self._check_student_access(user, student, school_id)

        exams = self.storage.get_exams_for_student(student_id, school_id)
        all_results = self.storage.get_all_exam_results_for_student(student_id, school_id)
        all_risks = self.storage.get_all_student_risks_for_student(student_id, school_id)

        return self.presenter.student_all_exams_success(student, exams, all_results, all_risks)

    # ---------------------------------------------------------------- helpers

    def _get_school_id(self, user):
        if user.role in ('ADMIN', 'PRINCIPAL'):
            profile = self.storage.get_principal_profile(user)
            if profile is None:
                raise NotFoundException('Principal/Admin profile not found.')
            return profile.school_id
        if user.role == 'TEACHER':
            teacher = getattr(user, 'teacherprofile', None)
            if teacher is None:
                raise NotFoundException('Teacher profile not found.')
            return teacher.school_id
        if user.role == 'STUDENT':
            student_profile = getattr(user, 'studentprofile', None)
            if student_profile is None:
                raise NotFoundException('Student profile not found.')
            return student_profile.school_id
        if user.role == 'PARENT':
            parent = getattr(user, 'parentprofile', None)
            if parent is None:
                raise NotFoundException('Parent profile not found.')
            return parent.school_id
        raise PermissionDeniedException('Access denied.')

    def _get_student(self, student_id, school_id):
        if not student_id:
            raise ValidationException('student_id is required.')
        student = self.storage.get_student_by_id(student_id, school_id)
        if student is None:
            raise StudentNotFoundError()
        return student

    def _get_done_exam_with_list(self, exam_id, school_id):
        """Returns (exam, exams_list). exam_id is required for student screens."""
        exams = self.storage.get_exams_for_school(school_id)
        if not exam_id:
            raise ValidationException('exam_id query parameter is required.')
        exam = self.storage.get_exam_by_id(exam_id, school_id)
        if exam is None:
            raise ExamNotFoundError()
        if exam.analytics_status != ANALYTICS_STATUS_DONE:
            raise AnalyticsValidationError(
                f'Analytics not ready (status: {exam.analytics_status}).'
            )
        return exam, exams

    def _check_student_access(self, user, student, school_id):
        """
        Enforce role-based access to an AnalyticsStudent record.

        PRINCIPAL/ADMIN  → always permitted (school already scoped).
        TEACHER          → student must belong to one of the teacher's assigned sections.
        STUDENT          → student.linked_user must be this user.
        PARENT           → student.linked_user must be one of this parent's linked children.
        """
        if user.role in ('ADMIN', 'PRINCIPAL'):
            return

        if user.role == 'TEACHER':
            teacher = getattr(user, 'teacherprofile', None)
            if teacher is None:
                raise NotFoundException('Teacher profile not found.')
            if student.section_id is None:
                raise PermissionDeniedException(
                    'This student has no linked section in the system.'
                )
            assigned_ids = list(teacher.assigned_sections.values_list('id', flat=True))
            if student.section_id not in assigned_ids:
                raise PermissionDeniedException(
                    'You can only view students in your assigned sections.'
                )
            return

        if user.role == 'STUDENT':
            if student.linked_user_id != user.id:
                raise PermissionDeniedException('You can only view your own analytics data.')
            return

        if user.role == 'PARENT':
            parent = getattr(user, 'parentprofile', None)
            if parent is None:
                raise NotFoundException('Parent profile not found.')
            if student.linked_user_id is None:
                raise PermissionDeniedException(
                    'This student is not yet linked to a portal account.'
                )
            # parent.students → M2M to StudentProfile; each StudentProfile has a user FK
            child_user_ids = list(parent.students.values_list('user_id', flat=True))
            if student.linked_user_id not in child_user_ids:
                raise PermissionDeniedException(
                    "You can only view your own child's analytics data."
                )
            return

        raise PermissionDeniedException('Access denied.')
