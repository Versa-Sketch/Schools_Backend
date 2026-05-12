from core.exceptions import NotFoundException, PermissionDeniedException
from analytics.constants import ANALYTICS_STATUS_DONE
from analytics.exceptions import AnalyticsValidationError, ExamNotFoundError


class StudentExamListInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def list(self, user):
        if user.role != 'STUDENT':
            raise PermissionDeniedException('Only students can access this endpoint.')
        analytics_student = self.storage.get_analytics_student_by_user(user)
        if analytics_student is None:
            return self.presenter.exam_list_success([])
        exams = self.storage.get_exams_for_student(analytics_student.id, analytics_student.school_id)
        return self.presenter.exam_list_success(exams)


class StudentExamSubjectsInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def list(self, user, exam_id):
        if user.role != 'STUDENT':
            raise PermissionDeniedException('Only students can access this endpoint.')
        analytics_student = self.storage.get_analytics_student_by_user(user)
        if analytics_student is None:
            raise NotFoundException('No analytics profile found for this student.')

        exam = self.storage.get_exam_by_id(exam_id, analytics_student.school_id)
        if exam is None:
            raise ExamNotFoundError()
        if exam.analytics_status != ANALYTICS_STATUS_DONE:
            raise AnalyticsValidationError(
                f'Analytics not ready (status: {exam.analytics_status}).'
            )

        subjects = self.storage.get_subjects_for_student_exam(exam_id, analytics_student.id)
        return self.presenter.exam_subjects_success(exam, subjects)


class StudentSubjectQuestionsInteractor:
    def __init__(self, storage, presenter):
        self.storage = storage
        self.presenter = presenter

    def list(self, user, exam_id, subject_id):
        if user.role != 'STUDENT':
            raise PermissionDeniedException('Only students can access this endpoint.')
        analytics_student = self.storage.get_analytics_student_by_user(user)
        if analytics_student is None:
            raise NotFoundException('No analytics profile found for this student.')

        exam = self.storage.get_exam_by_id(exam_id, analytics_student.school_id)
        if exam is None:
            raise ExamNotFoundError()
        if exam.analytics_status != ANALYTICS_STATUS_DONE:
            raise AnalyticsValidationError(
                f'Analytics not ready (status: {exam.analytics_status}).'
            )

        exam_subject = self.storage.get_exam_subject_by_id(subject_id, exam_id)
        if exam_subject is None:
            raise NotFoundException('Subject not found for this exam.')

        question_results = self.storage.get_question_results_by_student_id(
            exam_id, analytics_student.id, subject_id
        )
        return self.presenter.subject_questions_success(exam, exam_subject, question_results)
